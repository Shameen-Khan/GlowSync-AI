// All image processing and face landmarks remain in page memory.
const $=q=>document.querySelector(q);
const OUTLINES={
 lips:[[61,146,91,181,84,17,314,405,321,375,291,409,270,269,267,0,37,39,40,185]],
 eyes:[[33,7,163,144,145,153,154,155,133,173,157,158,159,160,161,246],[263,249,390,373,374,380,381,382,362,398,384,385,386,387,388,466]],
 brows:[[70,63,105,66,107,55,65,52,53,46],[300,293,334,296,336,285,295,282,283,276]],
 face:[[10,338,297,332,284,251,389,356,454,323,361,288,397,365,379,378,400,377,152,148,176,149,150,136,172,58,132,93,234,127,162,21,54,103,67,109]],
};
let videoStream=null,detectorPromise=null,landmarks=null,source=null,generation=0,callbacks=null;
const toneReferences=[['fair',[232,192,168]],['light',[211,167,137]],['medium',[184,134,100]],['tan',[143,99,71]],['deep',[92,61,47]]];

export function stopCamera(){
 if(videoStream)videoStream.getTracks().forEach(t=>t.stop());videoStream=null;
 const video=$('#camera-video');if(video){video.srcObject=null;video.hidden=true;}
 $('#capture-photo').hidden=true;$('#start-camera').hidden=false;
 if(source)$('#photo-canvas').hidden=false;else $('#photo-placeholder').hidden=false;
}
function status(message){$('#photo-status').textContent=message;}
function clearPhoto(){generation++;landmarks=null;source=null;stopCamera();const c=$('#photo-canvas');c.getContext('2d').clearRect(0,0,c.width,c.height);c.width=1;c.height=1;c.hidden=true;$('#photo-placeholder').hidden=false;$('#remove-photo').hidden=true;$('#photo-file').value='';status('Photos stay in this tab. They are never uploaded.');}
function detect(){
 if(!detectorPromise)detectorPromise=(async()=>{
  const {FaceLandmarker,FilesetResolver}=await import('/static/vendor/mediapipe/vision_bundle.mjs');
  const files=await FilesetResolver.forVisionTasks('/static/vendor/mediapipe/wasm');
  return FaceLandmarker.createFromOptions(files,{baseOptions:{modelAssetPath:'/static/vendor/mediapipe/face_landmarker.task',delegate:'CPU'},runningMode:'IMAGE',numFaces:2,minFaceDetectionConfidence:.5,minFacePresenceConfidence:.5,outputFaceBlendshapes:false,outputFacialTransformationMatrixes:false});
 })().catch(e=>{detectorPromise=null;throw e;});
 return detectorPromise;
}
function draw(){
 const c=$('#photo-canvas'),ctx=c.getContext('2d');ctx.clearRect(0,0,c.width,c.height);if(!source)return;ctx.drawImage(source,0,0);
 if(!landmarks)return;
 const colours={face:'#fff8e4',lips:'#f699b1',eyes:'#e8d39c',brows:'#d1dfb6'};
 for(const region of ['face','brows','eyes','lips'])for(const outline of OUTLINES[region]){
  ctx.beginPath();outline.forEach((index,i)=>{const p=landmarks[index];if(i===0)ctx.moveTo(p.x*c.width,p.y*c.height);else ctx.lineTo(p.x*c.width,p.y*c.height);});ctx.closePath();ctx.strokeStyle=colours[region];ctx.lineWidth=Math.max(1.8,c.width/400);ctx.shadowColor='#493234';ctx.shadowBlur=3;ctx.stroke();ctx.shadowBlur=0;
 }
}
function sampleTone(x,y){
 if(!source)return;
 const ctx=source.getContext('2d',{willReadFrequently:true}),radius=Math.max(3,Math.round(source.width*.008));
 const xx=Math.max(radius,Math.min(source.width-radius-1,Math.round(x*source.width))),yy=Math.max(radius,Math.min(source.height-radius-1,Math.round(y*source.height)));
 const pixels=ctx.getImageData(xx-radius,yy-radius,radius*2+1,radius*2+1).data;const channels=[[],[],[]];
 for(let i=0;i<pixels.length;i+=4)if(pixels[i+3]>200)for(let k=0;k<3;k++)channels[k].push(pixels[i+k]);
 if(!channels[0].length)return;
 const rgb=channels.map(a=>a.sort((a,b)=>a-b)[Math.floor(a.length/2)]);
 const tone=toneReferences.map(([label,ref])=>[label,ref.reduce((sum,v,i)=>sum+(v-rgb[i])**2,0)]).sort((a,b)=>a[1]-b[1])[0][0];
 callbacks.onTone(tone);
 return tone;
}
async function analyse(image){
 const token=++generation;landmarks=null;stopCamera();
 const width=image.videoWidth||image.naturalWidth||image.width,height=image.videoHeight||image.naturalHeight||image.height;
 if(!width||!height)throw new Error('The photo could not be read. Try a JPEG or PNG.');
 if(width*height>40000000)throw new Error('Choose a photo smaller than 40 megapixels.');
 const scale=Math.min(1,1400/Math.max(width,height));source=document.createElement('canvas');source.width=Math.round(width*scale);source.height=Math.round(height*scale);source.getContext('2d',{willReadFrequently:true}).drawImage(image,0,0,source.width,source.height);
 const c=$('#photo-canvas');c.width=source.width;c.height=source.height;c.hidden=false;$('#photo-placeholder').hidden=true;$('#remove-photo').hidden=false;draw();
 status('Finding face features on your device… the first photo may take a moment.');
 try{
  const model=await detect();if(token!==generation||!source)return;
  const result=model.detect(source);if(token!==generation)return;
  if(result.faceLandmarks.length===0){status('No face found. Try a clear, front-facing portrait or choose a feature manually.');return;}
  if(result.faceLandmarks.length!==1){status('More than one face found. Please use a photo of one person, or choose a feature manually.');return;}
  landmarks=result.faceLandmarks[0];draw();const p=landmarks[50];const tone=sampleTone(p.x,p.y);
  status(`Face found. Tap the outlined lips, eyes, brows or face. Suggested tone: ${tone}; adjust it if needed.`);
 }catch(error){if(token===generation)status('Face detection could not load. Your photo stays private. Choose a feature manually and set your tone.');}
}
export function pointInPolygon(point,polygon){let inside=false;for(let i=0,j=polygon.length-1;i<polygon.length;j=i++){const a=polygon[i],b=polygon[j];if((a.y>point.y)!==(b.y>point.y)&&point.x<(b.x-a.x)*(point.y-a.y)/(b.y-a.y)+a.x)inside=!inside;}return inside;}
export function canvasPoint(event,canvas){const rect=canvas.getBoundingClientRect(),scale=Math.min(rect.width/canvas.width,rect.height/canvas.height),w=canvas.width*scale,h=canvas.height*scale;const x=(event.clientX-rect.left-(rect.width-w)/2)/w,y=(event.clientY-rect.top-(rect.height-h)/2)/h;return x<0||y<0||x>1||y>1?null:{x,y};}
export function regionAt(point,points){if(!point||!points)return null;for(const region of ['lips','eyes','brows','face'])for(const path of OUTLINES[region])if(pointInPolygon(point,path.map(i=>points[i])))return region;return null;}
export function initStudio(handlers){
 callbacks=handlers;
 $('#upload-photo').addEventListener('click',()=>$('#photo-file').click());
 $('#photo-file').addEventListener('change',async event=>{
  const file=event.target.files[0];if(!file)return;
  if(!['image/jpeg','image/png','image/webp'].includes(file.type)||file.size>12*1024*1024){handlers.onError('Choose a JPEG, PNG or WebP photo smaller than 12 MB.');event.target.value='';return;}
  const url=URL.createObjectURL(file),img=new Image();
  try{img.src=url;await img.decode();await analyse(img);}catch(e){handlers.onError(e.message);}finally{URL.revokeObjectURL(url);event.target.value='';}
 });
 $('#start-camera').addEventListener('click',async()=>{
  try{
   stopCamera();if(!navigator.mediaDevices?.getUserMedia)throw new Error('Camera is unavailable. Open the localhost address or upload a photo.');
   videoStream=await navigator.mediaDevices.getUserMedia({video:{facingMode:'user',width:{ideal:1280},height:{ideal:960}},audio:false});
   const video=$('#camera-video');video.srcObject=videoStream;video.hidden=false;$('#photo-canvas').hidden=true;$('#photo-placeholder').hidden=true;await video.play();$('#capture-photo').hidden=false;$('#start-camera').hidden=true;$('#remove-photo').hidden=false;status('Camera preview is active. Capture when you are ready; the photo stays in this tab.');
  }catch(e){stopCamera();status('Camera could not open. Allow camera access or upload a photo instead.');handlers.onError(e.name==='NotAllowedError'?'Camera permission was not granted. You can upload a photo instead.':e.message);}
 });
 $('#capture-photo').addEventListener('click',async()=>{
  const video=$('#camera-video');if(!video.videoWidth){handlers.onError('Wait for the camera preview to appear.');return;}
  const capture=document.createElement('canvas');capture.width=video.videoWidth;capture.height=video.videoHeight;capture.getContext('2d').drawImage(video,0,0);try{await analyse(capture);}catch(e){handlers.onError(e.message);}
 });
 $('#remove-photo').addEventListener('click',clearPhoto);
 $('#photo-canvas').addEventListener('click',event=>{
  if(!landmarks)return;const point=canvasPoint(event,event.currentTarget),region=regionAt(point,landmarks);if(!region){status('Tap inside an outlined face feature, or use the feature buttons.');return;}
  if(region==='face'){const tone=sampleTone(point.x,point.y);status(`Face selected. Suggested tone: ${tone}; please correct it if needed.`);}else status(`${region==='brows'?'Eyebrows':region[0].toUpperCase()+region.slice(1)} selected. Your skin-tone setting is unchanged.`);
  handlers.onRegion(region);
 });
 window.addEventListener('pagehide',()=>{clearPhoto();});
 document.addEventListener('visibilitychange',()=>{if(document.hidden)stopCamera();});
}
