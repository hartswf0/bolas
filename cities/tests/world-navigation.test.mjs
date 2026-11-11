// Run with: node --test cities/tests/world-navigation.test.mjs
// Lightweight event and camera doubles exercise ownership/input contracts without a GPU.
import assert from 'node:assert/strict';
import {createWorldNavigation} from '../world-navigation.js';
let clock = 0;
class Target {
  constructor() { this.events = new Map(); this.dataset={}; this.attrs={}; this.style={touchAction:'pan-y',setProperty(k,v){this[k]=v}}; this.captures = new Set(); }
  addEventListener(k,f,o) { const a=this.events.get(k)||[]; a.push({f,c:o===true||o?.capture}); this.events.set(k,a); }
  removeEventListener(k,f) { this.events.set(k,(this.events.get(k)||[]).filter(e=>e.f!==f)); }
  dispatchEvent(e) { e.target??=this; e.preventDefault??=()=>{e.prevented=true}; e.stopPropagation??=()=>{}; e.stopImmediatePropagation??=()=>{e.stopped=true}; for(const h of [...(this.events.get(e.type)||[])].sort((a,b)=>Number(b.c)-Number(a.c))){if(e.stopped)break;h.f(e)} return !e.prevented; }
  setAttribute(k,v){this.attrs[k]=v} getAttribute(k){return this.attrs[k]??null} removeAttribute(k){delete this.attrs[k]}
  getBoundingClientRect(){return {left:0,top:0,width:800,height:600}} setPointerCapture(id){this.captures.add(id)} hasPointerCapture(id){return this.captures.has(id)} releasePointerCapture(id){this.captures.delete(id)} focus(){} closest(){return null}
}
class Euler {constructor(x,y,z,order){this.set(x,y,z,order)}set(x,y,z,order){Object.assign(this,{x,y,z,order});return this}}
const doc=new Target(), win=new Target(); doc.defaultView=win; doc.hidden=false; win.performance={now:()=>clock}; win.MouseEvent=class{constructor(type,fields){Object.assign(this,{type},fields)}};
const canvas=new Target(); canvas.ownerDocument=doc;
const camera={position:{x:99,y:99,z:99,set(x,y,z){Object.assign(this,{x,y,z})}},quaternion:{setFromEuler(e){this.euler={...e}}}};
const notices=[];const nav=createWorldNavigation({THREE:{Euler},camera,canvas,onChange:n=>notices.push(n)});
const fire=(target,type,fields={})=>target.dispatchEvent({type,...fields});
const key=(code,type='keydown',fields={})=>fire(win,type,{code,...fields});
const tick=(n=1)=>{for(let i=0;i<n;i++){clock+=50;nav.update(.05)}};
const room={id:'shelf',spawn:[0,-5.1,6],target:[0,-5.1,0],floorY:-6.8,bounds:{min:[-10,-10,-10],max:[10,10,10]},obstacles:[{min:[-2,-6.8,-2],max:[2,2,2]}]};
nav.enterRoom(room);key('KeyW');tick();assert.equal(camera.position.x,99,'guided never writes camera');
nav.setMode('walk');assert.equal(camera.position.y,-5.1);key('KeyW');tick(60);key('KeyW','keyup');assert.ok(Math.abs(nav.getPose().position[2]-2.35)<1e-9,'swept walk collision stops before shelf');
nav.setPose({position:[5,-5.1,6],yaw:0,pitch:0});key('KeyW');key('KeyD');const before=nav.getPose().position;tick();const after=nav.getPose().position;assert.ok(Math.hypot(after[0]-before[0],after[2]-before[2])<=4.5*.05+1e-9,'diagonal movement normalized');fire(win,'blur');
const stable=nav.getPose();tick();assert.deepEqual(nav.getPose(),stable,'blur releases movement');
key('KeyW');fire(doc,'focusin',{target:{closest:()=>({})}});tick();assert.deepEqual(nav.getPose(),stable,'form focus releases held keyboard movement');
key('KeyW','keydown',{target:{closest:()=>({})}});tick();assert.deepEqual(nav.getPose(),stable,'typing does not steer');
nav.setPose({position:[0,-5.1,6],yaw:0,pitch:0});nav.setMode('fly');key('KeyW');tick(45);key('KeyW','keyup');assert.ok(nav.getPose().position[2]<-2,'flight intentionally passes shelf');key('KeyE');tick(100);key('KeyE','keyup');assert.equal(nav.getPose().position[1],10,'flight ascent clamps at room ceiling');
const invalidBefore=nav.getPose();assert.equal(nav.setPose({position:[NaN,0,0],yaw:0,pitch:0}),false);assert.deepEqual(nav.getPose(),invalidBefore,'invalid import rejected');nav.setPose({position:[999,999,-999],yaw:999,pitch:999});assert.deepEqual(nav.getPose().position,[10,10,-10]);assert.ok(nav.getPose().pitch<Math.PI/2);
nav.enterRoom({...room,obstacles:[]});nav.setMode('walk');
let selections=0;canvas.addEventListener('click',()=>selections++);
fire(canvas,'pointerdown',{pointerId:1,pointerType:'mouse',button:0,clientX:400,clientY:300});fire(canvas,'pointermove',{pointerId:1,clientX:450,clientY:300});assert.ok(nav.isDragging);fire(canvas,'pointerup',{pointerId:1});fire(canvas,'click',{detail:1});assert.equal(selections,0,'look drag suppresses accidental archive pick');
key('KeyF');assert.equal(selections,1,'F interacts through center raycast');clock+=500;fire(canvas,'click',{detail:1});assert.equal(selections,2,'later ordinary click preserved');
const joystick=new Target(), up=new Target();nav.attachControls({joystick,ascend:up});nav.setPose({position:[0,-5.1,6],yaw:0,pitch:0});
fire(joystick,'pointerdown',{pointerId:2,pointerType:'touch',clientX:100,clientY:100});fire(joystick,'pointermove',{pointerId:2,clientX:100,clientY:50});fire(canvas,'pointerdown',{pointerId:3,pointerType:'touch',clientX:500,clientY:300});fire(canvas,'pointermove',{pointerId:3,clientX:550,clientY:300});const multiBefore=nav.getPose();tick();assert.notDeepEqual(nav.getPose().position,multiBefore.position,'two thumbs move and look concurrently');fire(canvas,'pointerup',{pointerId:3});const continued=nav.getPose();tick();assert.notDeepEqual(nav.getPose().position,continued.position,'releasing look thumb keeps move thumb');fire(joystick,'pointercancel',{pointerId:2});const cancelled=nav.getPose();tick();assert.deepEqual(nav.getPose(),cancelled,'pointer cancel releases movement');
nav.setMode('guided');camera.position.set(88,88,88);tick();assert.equal(camera.position.x,88);nav.setMode('walk');assert.deepEqual(nav.getPose(),cancelled,'guided returns to same manual pose');
nav.setEnabled(false);key('KeyW');camera.position.set(44,44,44);tick();assert.equal(camera.position.x,44,'disabled settings mode leaves camera');nav.setEnabled(true);
nav.setMode('fly');fire(up,'pointerdown',{pointerId:8,pointerType:'touch',button:0});const upBefore=nav.getPose().position[1];tick();assert.ok(nav.getPose().position[1]>upBefore,'touch ascent works');fire(up,'pointerup',{pointerId:8});
key('KeyW');doc.hidden=true;fire(doc,'visibilitychange');doc.hidden=false;fire(doc,'visibilitychange');const hidden=nav.getPose();tick();assert.deepEqual(nav.getPose(),hidden,'visibility interruption releases held movement');
nav.dispose();assert.equal(canvas.style.touchAction,'pan-y');assert.equal(joystick.style.touchAction,'pan-y');assert.equal(canvas.getAttribute('tabindex'),null);for(const target of [win,doc,joystick,up])assert.equal([...target.events.values()].reduce((n,a)=>n+a.length,0),0,'listeners removed');
console.log('PASS: guided isolation, walk collision, diagonal speed, focus/blur/visibility clearing, flight bounds, pose validation, tap/drag selection, center interaction, multitouch, mode continuity, disabled mode, ascent and disposal.');
