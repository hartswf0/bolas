/* title and end cards, in the same ink and paper */
(function (root) {
  root.Cards = {
    draw(ctx, which, lines) {
      const W = 1280, H = 720;
      ctx.fillStyle = '#efe4cc'; ctx.fillRect(0, 0, W, H);
      ctx.fillStyle = '#1b1714'; ctx.textAlign = 'left';
      if (which === 'title') {
        ctx.font = '600 22px "JetBrains Mono"'; ctx.fillText('PAE-02 · SCION 19 · Moho Pro — Smart-Bone Character Laboratory', 90, 150);
        ctx.font = '800 92px "Big Shoulders Display"'; ctx.fillText('THE THRESHOLD', 86, 250);
        ctx.font = 'italic 400 27px Literata'; ctx.fillText('a dog at a door that may refuse, built as a bone rig with corrective Smart Bones', 90, 300);
        ctx.fillText('and switch-layer head drawings, in one ink line over flat fills', 90, 336);
      } else {
        ctx.font = '600 20px "JetBrains Mono"'; ctx.fillText('WHAT THIS IS MADE OF', 90, 110);
        ctx.font = '400 21px Literata';
        lines.forEach((l, k) => ctx.fillText(l, 90, 160 + k * 37));
      }
      return true;
    }
  };
})(window);
