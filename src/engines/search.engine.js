/**
 * search.engine.js —— 全文检索（bigram + TF-IDF）
 *
 * 古籍没有空格，按词切不了，所以用二元字组（bigram）当索引单元：
 * 「师事阳明」→ 师事 / 事阳 / 阳明。这样「阳明」能命中，
 * 「明儒」也能命中，不需要分词器。
 *
 * 六十三卷共约 250 万字，全量索引在浏览器里跑得动，
 * 但要按卷增量建，不能一次性阻塞主线程。
 */
export function createIndex() {
  const tf = new Map();     // term -> Map<vol, count>
  const df = new Map();     // term -> 出现过的卷数
  const volumes = new Set();

  function bigrams(s) {
    const clean = String(s).replace(/[\s\p{P}]/gu, '');
    const out = [];
    for (let i = 0; i + 1 < clean.length; i++) out.push(clean.slice(i, i + 2));
    return out;
  }

  return {
    bigrams,
    get size() { return volumes.size; },

    add(vol, text) {
      if (volumes.has(vol)) return;
      volumes.add(vol);
      const local = new Map();
      for (const g of bigrams(text)) local.set(g, (local.get(g) || 0) + 1);
      for (const [g, c] of local) {
        if (!tf.has(g)) tf.set(g, new Map());
        tf.get(g).set(vol, c);
        df.set(g, (df.get(g) || 0) + 1);
      }
    },

    /** 返回 [{vol, score}]，按相关度降序 */
    search(query, limit = 20) {
      const grams = bigrams(query);
      if (!grams.length) return [];
      const N = volumes.size || 1;
      const score = new Map();
      for (const g of grams) {
        const post = tf.get(g);
        if (!post) continue;
        const idf = Math.log(1 + N / (1 + (df.get(g) || 0)));
        for (const [vol, c] of post) {
          score.set(vol, (score.get(vol) || 0) + Math.log(1 + c) * idf);
        }
      }
      return [...score.entries()]
        .map(([vol, s]) => ({ vol, score: +s.toFixed(3) }))
        .sort((a, b) => b.score - a.score)
        .slice(0, limit);
    },

    /** 命中处的上下文片段，供结果列表展示 */
    excerpt(text, query, radius = 36, max = 3) {
      const q = String(query).replace(/[\s\p{P}]/gu, '');
      if (!q) return [];
      const out = [];
      let from = 0;
      while (out.length < max) {
        const i = text.indexOf(q, from);
        if (i < 0) break;
        out.push({
          before: text.slice(Math.max(0, i - radius), i),
          hit: text.slice(i, i + q.length),
          after: text.slice(i + q.length, i + q.length + radius),
          at: i,
        });
        from = i + q.length;
      }
      return out;
    },

    clear() { tf.clear(); df.clear(); volumes.clear(); },
  };
}
