/**
 * Sound Effects (Web Audio API — no external files needed)
 */
const SFX = (() => {
    let ctx = null;

    function getCtx() {
        if (!ctx) ctx = new (window.AudioContext || window.webkitAudioContext)();
        return ctx;
    }

    function play(fn) {
        try { fn(getCtx()); } catch(e) { /* audio not supported */ }
    }

    return {
        /** Short rising chime — correct answer */
        correct() {
            play(ctx => {
                const t = ctx.currentTime;
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(523, t);       // C5
                osc.frequency.setValueAtTime(659, t + 0.1);  // E5
                osc.frequency.setValueAtTime(784, t + 0.2);  // G5
                gain.gain.setValueAtTime(0.3, t);
                gain.gain.exponentialRampToValueAtTime(0.01, t + 0.4);
                osc.connect(gain).connect(ctx.destination);
                osc.start(t);
                osc.stop(t + 0.4);
            });
        },

        /** Short descending buzz — wrong answer */
        wrong() {
            play(ctx => {
                const t = ctx.currentTime;
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'square';
                osc.frequency.setValueAtTime(300, t);
                osc.frequency.setValueAtTime(200, t + 0.15);
                gain.gain.setValueAtTime(0.15, t);
                gain.gain.exponentialRampToValueAtTime(0.01, t + 0.3);
                osc.connect(gain).connect(ctx.destination);
                osc.start(t);
                osc.stop(t + 0.3);
            });
        },

        /** Confirm lock sound — soft click */
        confirm() {
            play(ctx => {
                const t = ctx.currentTime;
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(880, t);
                gain.gain.setValueAtTime(0.15, t);
                gain.gain.exponentialRampToValueAtTime(0.01, t + 0.08);
                osc.connect(gain).connect(ctx.destination);
                osc.start(t);
                osc.stop(t + 0.1);
            });
        },

        /** Fanfare — quiz complete with good score */
        fanfare() {
            play(ctx => {
                const t = ctx.currentTime;
                const notes = [523, 659, 784, 1047]; // C5 E5 G5 C6
                notes.forEach((freq, i) => {
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    osc.type = 'sine';
                    osc.frequency.setValueAtTime(freq, t + i * 0.12);
                    gain.gain.setValueAtTime(0, t);
                    gain.gain.linearRampToValueAtTime(0.25, t + i * 0.12);
                    gain.gain.exponentialRampToValueAtTime(0.01, t + i * 0.12 + 0.5);
                    osc.connect(gain).connect(ctx.destination);
                    osc.start(t + i * 0.12);
                    osc.stop(t + i * 0.12 + 0.5);
                });
            });
        },

        /** Sparkle — badge unlock */
        sparkle() {
            play(ctx => {
                const t = ctx.currentTime;
                const notes = [1047, 1319, 1568, 2093]; // C6 E6 G6 C7
                notes.forEach((freq, i) => {
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    osc.type = 'sine';
                    osc.frequency.setValueAtTime(freq, t + i * 0.08);
                    gain.gain.setValueAtTime(0.2, t + i * 0.08);
                    gain.gain.exponentialRampToValueAtTime(0.01, t + i * 0.08 + 0.3);
                    osc.connect(gain).connect(ctx.destination);
                    osc.start(t + i * 0.08);
                    osc.stop(t + i * 0.08 + 0.3);
                });
            });
        },

        /** Level up — ascending arpeggio */
        levelUp() {
            play(ctx => {
                const t = ctx.currentTime;
                const notes = [523, 659, 784, 1047, 1319]; // C5 E5 G5 C6 E6
                notes.forEach((freq, i) => {
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    osc.type = 'triangle';
                    osc.frequency.setValueAtTime(freq, t + i * 0.1);
                    gain.gain.setValueAtTime(0.2, t + i * 0.1);
                    gain.gain.exponentialRampToValueAtTime(0.01, t + i * 0.1 + 0.4);
                    osc.connect(gain).connect(ctx.destination);
                    osc.start(t + i * 0.1);
                    osc.stop(t + i * 0.1 + 0.4);
                });
            });
        },
    };
})();
