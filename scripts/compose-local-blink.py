"""Calibrated eyelid occlusion on an accepted talking-head video.

Run in the existing SadTalker Python environment (OpenCV/NumPy/Pillow).
Generated closed-eye material supplies skin and eyelid lines only. The live
eyeballs remain stationary beneath a moving lid. This is video compositing,
not another full-face model pass. It is deliberately not an automatic face rig.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_image(path):
    return cv2.imdecode(np.frombuffer(path.read_bytes(), np.uint8), cv2.IMREAD_COLOR)


def save_image(path, image):
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, data = cv2.imencode('.png', image)
    if not ok:
        raise RuntimeError('PNG encoding failed')
    path.write_bytes(data.tobytes())


def smoothstep(lo, hi, x):
    t = np.clip((x - lo) / np.maximum(hi - lo, 1e-5), 0, 1)
    return t * t * (3 - 2 * t)


def eye_shift(reference, frame, eye):
    x0, y0, x1, y1 = eye['tracking_roi']
    a = cv2.cvtColor(reference[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    b = cv2.cvtColor(frame[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    mask = np.ones(a.shape, np.uint8) * 255
    ex0, ey0, ex1, ey1 = eye['tracking_exclusion']
    mask[max(ey0-y0, 0):ey1-y0, max(ex0-x0, 0):ex1-x0] = 0
    score, matrix = cv2.findTransformECC(a, b, np.eye(2, 3, dtype=np.float32),
        cv2.MOTION_TRANSLATION, (cv2.TERM_CRITERIA_COUNT | cv2.TERM_CRITERIA_EPS, 60, 1e-5), mask, 5)
    dx, dy = map(float, matrix[:, 2])
    if score < .85 or max(abs(dx), abs(dy)) > 5:
        raise ValueError(f"Unreliable local tracking for {eye['name']}: {score}, {dx}, {dy}")
    return dx, dy, float(score)


def compose(frame, reference, donor, closure, eyes):
    """Move opaque eyelid material; never blend two different iris appearances."""
    result = frame.copy()
    support = np.zeros(frame.shape[:2], np.uint8)
    tracking = []
    if closure == 0:
        return result, support, tracking
    for eye in eyes:
        dx, dy, score = eye_shift(reference, frame, eye)
        tracking.append({'eye': eye['name'], 'dx': dx, 'dy': dy, 'correlation': score})
        xs = np.array(eye['x'], np.float32)
        x0, x1 = int(xs[0]-2), int(xs[-1]+3)
        y0 = int(min(eye['upper_open'])-32)
        y1 = int(max(eye['lower_open'])+16)
        # A padded box is only the work area. The actual support stays within
        # two eyelid contours and excludes brows, nose, jaw, lips and glasses.
        bx0, bx1 = x0-6, x1+6
        by0, by1 = y0-6, y1+6
        yy, xx = np.mgrid[by0:by1, bx0:bx1].astype(np.float32)
        local_x, local_y = xx-dx, yy-dy
        upper = np.interp(local_x, xs, eye['upper_open']).astype(np.float32)
        half = np.interp(local_x, xs, eye['upper_half']).astype(np.float32)
        closed = np.interp(local_x, xs, eye['closed']).astype(np.float32)
        lower = np.interp(local_x, xs, eye['lower_open']).astype(np.float32)
        if closure <= .5:
            edge = upper + (half-upper) * (closure*2)
        else:
            edge = half + (closed-half) * ((closure-.5)*2)
        bottom_edge = lower + (closed+4-lower) * closure**1.6
        # Feather must finish above the ORIGINAL upper lash, otherwise a
        # second open-eye arc survives while the new lid descends.
        top = upper-28
        bottom = lower+12
        horizontal = smoothstep(xs[0], xs[0]+10, local_x) * (1-smoothstep(xs[-1]-10, xs[-1], local_x))
        top_feather = smoothstep(top, top+10, local_y)
        bottom_feather = 1-smoothstep(bottom-9, bottom, local_y)
        # Closed-eye texture is remapped above the moving lash line. Only the
        # skin strip changes height; the live pupil is never rescaled.
        src_y = np.where(local_y <= edge,
            top + (local_y-top) * (closed-top) / np.maximum(edge-top, 1),
            closed + local_y-edge).astype(np.float32)
        upper_material = cv2.remap(donor, local_x, src_y, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT_101)
        upper_alpha = horizontal * top_feather * (1-smoothstep(edge+2, edge+6, local_y))
        src_lower_y = (closed+4 + local_y-bottom_edge).astype(np.float32)
        lower_material = cv2.remap(donor, local_x, src_lower_y, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT_101)
        lower_alpha = horizontal * bottom_feather * smoothstep(bottom_edge-1, bottom_edge+3, local_y) * closure
        patch = result[by0:by1, bx0:bx1].astype(np.float32)
        patch = patch*(1-lower_alpha[..., None]) + lower_material.astype(np.float32)*lower_alpha[..., None]
        patch = patch*(1-upper_alpha[..., None]) + upper_material.astype(np.float32)*upper_alpha[..., None]
        # Explicitly zero the feather outside its finite support. No Gaussian
        # infinite tails, no processing outside eye contours.
        active = (upper_alpha > 0) | (lower_alpha > 0)
        patch[~active] = frame[by0:by1, bx0:bx1][~active]
        result[by0:by1, bx0:bx1] = np.clip(np.rint(patch), 0, 255).astype(np.uint8)
        support[by0:by1, bx0:bx1][active] = 255
    return result, support, tracking


def contact_sheet(frames, path, *, eyes=False, cols=5):
    width, height = (490, 178) if eyes else (300, 300)
    scale = 1.5 if eyes else 1
    width, height = int(width*scale), int(height*scale)
    rows = (len(frames)+cols-1)//cols
    sheet = Image.new('RGB', (cols*width, rows*(height+28)), (22, 27, 35))
    draw = ImageDraw.Draw(sheet)
    for k, (label, frame) in enumerate(frames):
        a = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if eyes:
            a = a.crop((390, 554, 880, 732))
        a = a.resize((width, height), Image.Resampling.LANCZOS)
        x, y = k % cols*width, k//cols*(height+28)
        sheet.paste(a, (x, y+28))
        draw.text((x+8, y+7), label, fill='white')
    sheet.save(path)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--config', type=Path, default=Path('config/ade-blink-round08.json'))
    p.add_argument('--output', type=Path, default=Path('outputs/round08'))
    p.add_argument('--keyframes-only', action='store_true')
    args = p.parse_args()
    start = time.perf_counter()
    cfg = json.loads(args.config.read_text(encoding='utf-8'))
    dest = args.output.resolve()
    if not dest.is_relative_to(ROOT/'outputs'):
        raise ValueError('Output must be a new private outputs directory')
    dest.mkdir(parents=True, exist_ok=True)
    if (dest/'head_local_blink.mp4').exists():
        raise FileExistsError('Preserve the existing version; select a new output directory')
    src = ROOT/cfg['source_video']
    audio = ROOT/cfg['source_audio']
    for path, expected in [(src, cfg['source_video_sha256']), (audio, cfg['source_audio_sha256'])]:
        if digest(path) != expected:
            raise ValueError(f'Accepted source hash mismatch: {path.name}')
    reference = load_image(ROOT/cfg['reference_image'])
    donor = load_image(ROOT/cfg['closed_reference'])
    if reference.shape != donor.shape or reference.shape[:2] != tuple(cfg['size'][::-1]):
        raise ValueError('Reference dimensions must match; do not silently resize the identity')
    cv2.setNumThreads(1)
    keys = []
    for label, amount in [('open', 0), ('half', .5), ('closed', 1)]:
        key, _, _ = compose(reference, reference, donor, amount, cfg['eyes'])
        save_image(dest/f'key_{label}.png', key)
        keys.append((label, key))
    contact_sheet(keys, dest/'keyframes.png', cols=3)
    contact_sheet(keys, dest/'keyframes_eyes.png', eyes=True, cols=3)
    if args.keyframes_only:
        print(json.dumps({'stage': 'composited-keyframes', 'output': str(dest), 'elapsed_sec': time.perf_counter()-start}))
        return
    qa = dest/'qa'
    qa.mkdir(exist_ok=True)
    w, h = cfg['size']
    output = dest/'head_local_blink.mp4'
    encoder = subprocess.Popen([str(ROOT/'tools/bin/ffmpeg.exe'), '-nostdin', '-v', 'error', '-n',
        '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-video_size', f'{w}x{h}', '-framerate', str(cfg['fps']),
        '-i', 'pipe:0', '-i', str(src), '-map', '0:v:0', '-map', '1:a:0',
        '-c:v', 'libx264', '-crf', '12', '-preset', 'fast', '-threads', '2', '-pix_fmt', 'yuv420p',
        '-c:a', 'copy', '-movflags', '+faststart', str(output)], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    cap = cv2.VideoCapture(str(src.relative_to(ROOT)))
    if abs(cap.get(cv2.CAP_PROP_FPS)-cfg['fps']) > 1e-6:
        raise ValueError('FPS mismatch')
    records, frames, union = [], [], np.zeros((h, w), np.uint8)
    i = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            phase = i-cfg['blink_start_frame']
            closure = cfg['closure'][phase] if 0 <= phase < len(cfg['closure']) else 0
            result, support, tracking = compose(frame, reference, donor, closure, cfg['eyes'])
            delta = np.abs(result.astype(np.int16)-frame.astype(np.int16))
            outside_max = int(delta[support == 0].max())
            if outside_max:
                raise AssertionError('Uncompressed pixels changed outside eyelid support')
            union = cv2.bitwise_or(union, support)
            records.append({'frame': i, 'time_sec': i/cfg['fps'], 'closure': closure,
                'outside_support_max_abs': outside_max, 'changed_pixels': int(np.any(delta, axis=2).sum()), 'tracking': tracking})
            encoder.stdin.write(result.tobytes())
            if cfg['blink_start_frame']-1 <= i <= cfg['blink_start_frame']+len(cfg['closure']):
                save_image(qa/f'preencode_f{i:03d}.png', result)
            i += 1
    finally:
        cap.release()
        encoder.stdin.close()
        err = encoder.stderr.read().decode('utf-8', errors='replace')
        encoder.wait()
    if encoder.returncode:
        raise RuntimeError(err)
    if i != cfg['frames']:
        raise ValueError(f'Expected {cfg["frames"]} frames, got {i}')
    save_image(qa/'eyelid_support_union.png', union)
    # Decode actual MP4 for evidence; do not use pre-encode PNGs as video proof.
    cap = cv2.VideoCapture(str(output.relative_to(ROOT)))
    original = cv2.VideoCapture(str(src.relative_to(ROOT)))
    sums, counts, maxima = {}, {}, {}
    decoded = 0
    regions = {'mouth_and_jaw': (410, 810, 830, 1130), 'brows': (380, 495, 875, 570)}
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        good, base = original.read()
        if not good:
            raise ValueError('Decoded time sequence diverges')
        diff = np.abs(frame.astype(np.int16)-base.astype(np.int16))
        for name, (x0, y0, x1, y1) in regions.items():
            values = diff[y0:y1, x0:x1]
            sums[name] = sums.get(name, 0)+int(values.sum())
            counts[name] = counts.get(name, 0)+values.size
            maxima[name] = max(maxima.get(name, 0), int(values.max()))
        if cfg['blink_start_frame']-1 <= decoded <= cfg['blink_start_frame']+len(cfg['closure']):
            save_image(qa/f'decoded_f{decoded:03d}.png', frame)
            frames.append((f'f{decoded:03d}  {decoded/cfg["fps"]:.2f}s', frame))
        decoded += 1
    cap.release()
    original.release()
    if decoded != cfg['frames']:
        raise ValueError('Decoded frame count mismatch')
    contact_sheet(frames, qa/'blink_sequence_eyes.png', eyes=True, cols=4)
    contact_sheet(frames, qa/'blink_sequence_full.png', cols=4)
    ffmpeg = str(ROOT/'tools/bin/ffmpeg.exe')
    pcm = []
    for path in [src, output]:
        r = subprocess.run([ffmpeg, '-v', 'error', '-i', str(path), '-map', '0:a:0', '-f', 's16le', '-ac', '1', '-ar', '16000', 'pipe:1'], capture_output=True, check=True)
        pcm.append(r.stdout)
    if pcm[0] != pcm[1]:
        raise AssertionError('Audio PCM differs from accepted baseline')
    decode = subprocess.run([ffmpeg, '-v', 'error', '-i', str(output), '-f', 'null', '-'], capture_output=True, check=True)
    if decode.stderr:
        raise AssertionError(decode.stderr.decode(errors='replace'))
    probe = subprocess.run([str(ROOT/'tools/bin/ffprobe.exe'), '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(output)], capture_output=True, check=True)
    report = {
        'schema_version': 1, 'source': cfg['source_video'], 'source_sha256': digest(src),
        'audio_source': cfg['source_audio'], 'audio_source_sha256': digest(audio),
        'output': output.relative_to(ROOT).as_posix(), 'output_sha256': digest(output),
        'method': 'generated closed-eyelid skin / moving opaque occlusion; piecewise open-half-closed lid geometry; live iris never rescaled or crossfaded',
        'config': args.config.as_posix(), 'config_sha256': digest(args.config),
        'half_reference_role': 'visual keyframe and manually calibrated halfway eyelid contour; no donor iris copied',
        'closed_reference_sha256': digest(ROOT/cfg['closed_reference']),
        'half_reference_sha256': digest(ROOT/cfg['half_reference']),
        'reference_image_sha256': digest(ROOT/cfg['reference_image']),
        'versions': {'opencv': cv2.__version__, 'numpy': np.__version__, 'image_gen_backend': 'not exposed by built-in tool'},
        'frames': i, 'decoded_frames': decoded, 'fps': cfg['fps'], 'duration_sec': i/cfg['fps'],
        'blink_start_sec': cfg['blink_start_frame']/cfg['fps'], 'closure_by_frame': cfg['closure'],
        'peak_frames': [cfg['blink_start_frame']+j for j,v in enumerate(cfg['closure']) if v == 1],
        'pcm_equal_to_baseline': True, 'pcm_sha256': hashlib.sha256(pcm[0]).hexdigest(),
        'full_decode_errors': 0, 'outside_support_max_abs_preencode': max(r['outside_support_max_abs'] for r in records),
        'encoded_rgb_difference': {k: {'mean_abs_0_255': sums[k]/counts[k], 'max_abs_0_255': maxima[k]} for k in regions},
        'difference_scope': 'preencode arrays exact outside eye mask; final H264 reencode introduces small spatial codec differences, not a model edit',
        'probe': json.loads(probe.stdout), 'frame_records': records,
        'elapsed_sec': time.perf_counter()-start, 'user_accepted': False, 'body_integrated': False,
        'subtitles_integrated': False, 'audio_stream_copied': True,
        'limitations': ['calibrated only for this 4.4s Ade sample', 'subjective naturalness pending user review', 'no long-video blink scheduling tested']}
    (dest/'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ['frame_records', 'probe']}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
