import { setTimeout as delay } from 'node:timers/promises';

export function withTimeout(promise, ms, label) {
  let timer;
  const timeout = new Promise((_, reject) => {
    timer = setTimeout(() => reject(Object.assign(new Error(`${label} timed out after ${ms / 1000}s`), { code: 'TURN_TIMEOUT' })), ms);
  });
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timer));
}

const terminations = new WeakMap();
export function terminateProcess(proc, graceMs = 5000) {
  if (!proc?.pid) return Promise.resolve();
  if (!terminations.has(proc)) terminations.set(proc, terminate(proc, graceMs));
  return terminations.get(proc);
}
async function terminate(proc, graceMs) {
  // All adapters spawn detached POSIX groups. A child may exit before its
  // descendants; signal the group even when the direct child's exit is known.
  const target = process.platform !== 'win32' && proc.__roundtableGroup !== false ? -proc.pid : proc.pid;
  const exists = pid => {
    try { process.kill(pid, 0); return true; }
    catch (error) { if (error.code === 'ESRCH') return false; if (error.code === 'EPERM') return true; throw error; }
  };
  const signal = name => { try { process.kill(target, name); } catch (error) { if (!['ESRCH', 'EPERM'].includes(error.code)) throw error; } };
  if (exists(target)) {
    signal('SIGTERM');
    const deadline = Date.now() + graceMs;
    while (exists(target) && Date.now() < deadline) await delay(10);
    if (exists(target)) signal('SIGKILL');
  }
  // EOF/group disappearance can precede the child's exit/reap event. Always
  // wait for our direct PID too, including the no-group early-exit case.
  const reapDeadline = Date.now() + Math.max(graceMs, 1000);
  while ((exists(proc.pid) || exists(target)) && Date.now() < reapDeadline) await delay(10);
  if (exists(proc.pid) || exists(target)) throw new Error(`process group ${proc.pid} remains after bounded cleanup`);
}
