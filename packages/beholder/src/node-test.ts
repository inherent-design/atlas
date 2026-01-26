import * as process from 'node:process'

console.log('1: sync')

setTimeout(() => console.log('7: setTimeout'), 0)

Promise.resolve()
  .then(() => console.log('3: microtask 1'))
  .then(() => console.log('4: microtask 2'))
setImmediate(() => console.log('5: setImmediate'))
process.nextTick(() => console.log('6: nextTick'))

console.log('2: sync end')

// Test: Is nextTick truly after microtasks in v24?
// Promise.resolve().then(() => {
//     console.log('A: microtask');
//     process.nextTick(() => console.log('B: nextTick from microtask'));
//     Promise.resolve().then(() => console.log('C: nested microtask'));
// });

// process.nextTick(() => console.log('D: top-level nextTick'));
