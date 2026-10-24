/* Continuous textured limbs: shared mesh vertices, no cut elbow/knee pieces.
   Every frame is a pure function of the paused GSAP timeline state. */
(function(){
  'use strict';
  const radians=d=>d*Math.PI/180;
  const smooth=x=>{x=Math.max(0,Math.min(1,x));return x*x*(3-2*x);};
  const softMax=(a,b)=>(a+b+Math.sqrt((a-b)*(a-b)+4))/2;
  function shader(gl,type,src){const s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;}

  class ContinuousPuppet {
    constructor(canvas,atlas,base,config,contours){
      this.canvas=canvas;this.base=base;this.config=config;this.parts={};
      const gl=canvas.getContext('webgl',{alpha:true,antialias:true,premultipliedAlpha:true,preserveDrawingBuffer:true});
      if(!gl)throw Error('WebGL unavailable; do not export an incomplete puppet.');
      this.gl=gl;
      const program=gl.createProgram();
      gl.attachShader(program,shader(gl,gl.VERTEX_SHADER,'attribute vec2 aPosition;attribute vec2 aUV;uniform vec2 resolution;uniform vec2 origin;varying vec2 uv;void main(){vec2 p=(aPosition+origin)/resolution;gl_Position=vec4(p.x*2.0-1.0,1.0-p.y*2.0,0.0,1.0);uv=aUV;}'));
      gl.attachShader(program,shader(gl,gl.FRAGMENT_SHADER,'precision mediump float;varying vec2 uv;uniform sampler2D image;void main(){gl_FragColor=texture2D(image,uv);}'));
      gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));
      this.program=program;gl.useProgram(program);
      this.pos=gl.getAttribLocation(program,'aPosition');this.uv=gl.getAttribLocation(program,'aUV');
      gl.uniform2f(gl.getUniformLocation(program,'resolution'),canvas.width,canvas.height);
      gl.uniform2f(gl.getUniformLocation(program,'origin'),...config.mesh.origin);
      gl.uniform1i(gl.getUniformLocation(program,'image'),0);
      gl.enable(gl.BLEND);gl.blendFunc(gl.ONE,gl.ONE_MINUS_SRC_ALPHA);
      gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL,true);
      for(const name of ['leg_left','leg_right','arm_left','arm_right']){
        const bind=base[name], [x0,y0,x1,y1]=bind.crop,w=x1-x0,h=y1-y0;
        const source=document.createElement('canvas');source.width=w;source.height=h;
        const ctx=source.getContext('2d');ctx.translate(-x0,-y0);ctx.clip(new Path2D(contours[name]));ctx.drawImage(atlas,0,0);
        const texture=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,texture);
        gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
        gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,source);
        const rows=[y0];for(let y=y0+config.mesh.source_row_step_px;y<y1;y+=config.mesh.source_row_step_px)rows.push(y);rows.push(y1);
        const coords=(contours[name].match(/-?\d*\.?\d+/g)||[]).map(Number),outline=[];
        for(let i=0;i<coords.length;i+=2)outline.push([coords[i],coords[i+1]]);
        const bounds=y=>{
          const hits=[];
          for(let i=0;i<outline.length;i++){const a=outline[i],b=outline[(i+1)%outline.length];if((a[1]<=y&&b[1]>y)||(b[1]<=y&&a[1]>y))hits.push(a[0]+(b[0]-a[0])*(y-a[1])/(b[1]-a[1]));}
          if(!hits.length){const nearest=outline.reduce((a,b)=>Math.abs(a[1]-y)<Math.abs(b[1]-y)?a:b);hits.push(nearest[0]);}
          return [Math.max(x0,Math.min(...hits)-3),Math.min(x1,Math.max(...hits)+3)];
        };
        const cols=config.mesh.columns,uv=[],indices=[];
        for(let r=0;r<rows.length;r++){const [lo,hi]=bounds(rows[r]);for(let c=0;c<=cols;c++)uv.push((lo+(hi-lo)*c/cols-x0)/w,(rows[r]-y0)/h);}
        for(let r=0;r<rows.length-1;r++)for(let c=0;c<cols;c++){const a=r*(cols+1)+c,b=a+1,d=a+cols+1,e=d+1;indices.push(a,b,e,a,e,d);}
        const p={name,bind,rows,cols,outline,texture,indices:new Uint16Array(indices),vertices:new Float32Array(uv.length),uv:new Float32Array(uv)};
        p.positionBuffer=gl.createBuffer();p.uvBuffer=gl.createBuffer();p.indexBuffer=gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER,p.uvBuffer);gl.bufferData(gl.ARRAY_BUFFER,p.uv,gl.STATIC_DRAW);
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,p.indexBuffer);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,p.indices,gl.STATIC_DRAW);
        this.parts[name]=p;
      }
      this.restFloor=softMax(this.geometry('leg_left',0,0).bottom,this.geometry('leg_right',0,0).bottom);
    }
    geometry(name,upperDeg,bendDeg){
      const p=this.parts[name],bind=p.bind,joint=this.config.joints[name];
      const upper=radians(upperDeg),bend=radians(bendDeg),[px,py]=bind.source_pivot;
      const theta=y=>upper+bend*smooth((y-joint.joint_source_y+joint.bend_halfwidth_px)/(joint.bend_halfwidth_px*2));
      const first=p.rows[0];let cx=-Math.sin(upper)*(first-py),cy=Math.cos(upper)*(first-py),last=first;
      const row=[];
      for(const y of p.rows){
        const n=Math.max(1,Math.ceil((y-last)/2)),step=(y-last)/n;
        for(let k=0;k<n;k++){const a=theta(last+(k+.5)*step);cx-=Math.sin(a)*step;cy+=Math.cos(a)*step;}
        const a=theta(y);row.push({y,cx,cy,a});last=y;
      }
      const at=(x,y)=>{
        const r=Math.min(row.length-2,Math.max(0,Math.floor((y-first)/this.config.mesh.source_row_step_px)));
        const l=row[r],h=row[r+1],w=(y-l.y)/(h.y-l.y),a=l.a+(h.a-l.a)*w;
        const xx=(l.cx+(h.cx-l.cx)*w)+Math.cos(a)*(x-px),yy=(l.cy+(h.cy-l.cy)*w)+Math.sin(a)*(x-px);
        return [bind.pivot[0]+xx*bind.scale,bind.pivot[1]+yy*bind.scale];
      };
      for(let r=0;r<row.length;r++)for(let c=0;c<=p.cols;c++){
        const i=(r*(p.cols+1)+c)*2,point=at(bind.crop[0]+(bind.crop[2]-bind.crop[0])*p.uv[i],row[r].y);
        p.vertices[i]=point[0];p.vertices[i+1]=point[1];
      }
      let minArea=Infinity,minRatio=Infinity;
      for(let i=0;i<p.indices.length;i+=3){
        const a=p.indices[i]*2,b=p.indices[i+1]*2,c=p.indices[i+2]*2;
        const area=(p.vertices[b]-p.vertices[a])*(p.vertices[c+1]-p.vertices[a+1])-(p.vertices[b+1]-p.vertices[a+1])*(p.vertices[c]-p.vertices[a]);
        minArea=Math.min(minArea,area);
        const uvarea=(p.uv[b]-p.uv[a])*(p.uv[c+1]-p.uv[a+1])-(p.uv[b+1]-p.uv[a+1])*(p.uv[c]-p.uv[a]);
        const rest=uvarea*(bind.crop[2]-bind.crop[0])*(bind.crop[3]-bind.crop[1])*bind.scale*bind.scale;
        minRatio=Math.min(minRatio,area/rest);
      }
      const jr=Math.max(0,Math.min(row.length-1,Math.round((joint.joint_source_y-first)/this.config.mesh.source_row_step_px)));
      const jl=jr*(p.cols+1)*2,jh=(jr*(p.cols+1)+p.cols)*2;
      const jointCenterX=bind.crop[0]+(p.uv[jl]+p.uv[jh])*.5*(bind.crop[2]-bind.crop[0]);
      const outline=p.outline.map(([x,y])=>at(x,y)),anchor=at(px,py),elbow=at(jointCenterX,joint.joint_source_y);
      return {p,bottom:Math.max(...outline.map(v=>v[1])),outline,anchor,joint:elbow,minArea,minRatio,upperDeg,bendDeg};
    }
    draw(state){
      const geometry={};
      for(const n of Object.keys(this.parts))geometry[n]=this.geometry(n,state[n+'_upper']||0,state[n+'_bend']||0);
      const dip=this.restFloor-softMax(geometry.leg_left.bottom,geometry.leg_right.bottom);
      const gl=this.gl;gl.viewport(0,0,this.canvas.width,this.canvas.height);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT);gl.useProgram(this.program);
      for(const {p} of Object.values(geometry)){
        gl.bindBuffer(gl.ARRAY_BUFFER,p.positionBuffer);gl.bufferData(gl.ARRAY_BUFFER,p.vertices,gl.DYNAMIC_DRAW);gl.enableVertexAttribArray(this.pos);gl.vertexAttribPointer(this.pos,2,gl.FLOAT,false,0,0);
        gl.bindBuffer(gl.ARRAY_BUFFER,p.uvBuffer);gl.enableVertexAttribArray(this.uv);gl.vertexAttribPointer(this.uv,2,gl.FLOAT,false,0,0);
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,p.indexBuffer);gl.bindTexture(gl.TEXTURE_2D,p.texture);gl.drawElements(gl.TRIANGLES,p.indices.length,gl.UNSIGNED_SHORT,0);
      }
      gl.finish();
      return {dip,geometry:Object.fromEntries(Object.entries(geometry).map(([name,g])=>[name,{anchor:g.anchor,joint:g.joint,min_triangle_area:g.minArea,min_area_ratio:g.minRatio,upper_deg:g.upperDeg,bend_deg:g.bendDeg,bottom:g.bottom}]))};
    }
  }
  window.ContinuousPuppet=ContinuousPuppet;
})();
