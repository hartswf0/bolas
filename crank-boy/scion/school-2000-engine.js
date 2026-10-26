// THE SCHOOL OF THE YEAR 2000 — pure, deterministic engine. Revision 2 (after independent critique).
// COUNTERFACTUAL world built from SCION Counterfuture A (the book as witness), with C actions.
// The "approved edition" and the inspector are invented; in 1909 the documented condemnation of
// history manuals came from the French bishops, not from a state inspector.
(function (root) {
  const PAGES = [
    "Histoire de France, cours moyen. Chapter XII: The canal of Saint-Aubin.",
    "The valley of Saint-Aubin lies between the hills and the river.",
    "Before the canal, grain went to market by cart, over a bad road.",
    "In 1828 the prefect asked Paris for a canal.",
    "The State sent its engineers.",
    "The canal was opened in 1834 by the engineers of the State.",
    "Barges now carried the grain to the city in half a day.",
    "The valley prospered and its population grew.",
    "Thus the works of the nation bring prosperity to its provinces.",
    "Questions. When was the canal opened? Who built it?"
  ];
  const CANAL = 5;
  const OLD_CANAL = "The canal was dug from 1829 and opened in 1832 by the men of the valley, requisitioned by the prefect for forty days a year.";
  const BOOK_LINE = "p. 112: “The canal was dug from 1829 and opened in 1832 by the men of the valley, requisitioned by the prefect for forty days a year. The engineers of the State drew the line and measured the locks.”";
  const MAX = PAGES.length;
  const DISTRACT = [3, 4];           // the master turns to write the date on the board

  const NOTES = {
    depends:  { t: "The master says the machine only reads what is in the hopper.", a: "A1" },
    edition:  { t: "Hopper volume: Édition de 1909. Your copy: Édition de 1876. Same title, same author.", a: "A2" },
    shelf:    { t: "Both editions are on the shelf. The 1876 printing sits on the top row, unused.", a: "A2" },
    crank:    { t: "With the cap off, the room is loud: the crank, and Émile breathing.", a: "A4" },
    nevercap: { t: "Émile turns the crank from eight to noon. He has never worn a cap.", a: "A4" },
    stop:     { t: "When Émile stopped, every pupil's lesson stopped on the same word.", a: "A4" },
    same:     { t: "Lucie heard the same sentence you did, word for word.", a: "A5" },
    paper:    { t: "Lucie: “The machine said it inside my head. Yours is only paper.”", a: "A6" },
    noone:    { t: "You said it out loud. No one wearing a cap heard you.", a: "A7" },
    nowait:   { t: "Reading under the cap, the voice kept going. There was no page to point to.", a: "A3" },
    hopper:   { t: "You loaded the hopper. The whole class heard your book's account of the canal.", a: "A2" },
    differ:   { t: "The editions disagree twice: 1832 or 1834, and whether the men who dug it are named.", a: "A4" },
    oral:     { t: "Émile: his grandfather dug on the canal and was still digging in 1833.", a: "A3" },
    notsource:{ t: "The master: a crank boy's grandfather is not a source.", a: "A6" }
  };
  const ASSUMPTIONS = {
    A1: "The machine replaces reading, not the book. It cannot run without one.",
    A2: "Whoever chooses the volume decides what the class knows. The picture gives that choice to the master and never shows it being made.",
    A3: "Transmitted knowledge carries no reference. A pupil can hold a sentence without being able to say where it came from, so it cannot be weighed against other witnesses.",
    A4: "Someone's labor powers the lesson and is left out of it: the crank in the room, the dug canal in the text.",
    A5: "Receiving the same thing is not checking it. Uniform delivery removes the comparison that would catch an error.",
    A6: "Access is not authority. The sentence is in every head; the right to say it is correct stays with the master and the edition.",
    A7: "Pupils receive and do not send. The apparatus has one input and no channel back."
  };

  function init() {
    return {
      tick: 0, cap: true, crank: true, loc: "seat",
      heardCanal: false, knowT: false, knowB: false,
      patience: 3, emile: 0, lucie: 0, asked: 0,
      hopper: "1909", fed: false, classHeardOld: false, emileBlamed: null,
      notes: [], log: [{ who: "wire", t: "The bell rings. The caps hum. Émile starts the crank." }],
      phase: "lesson", ending: null, objective: null
    };
  }
  const clone = s => JSON.parse(JSON.stringify(s));
  const note = (s, id) => { if (!s.notes.includes(id)) s.notes.push(id); };
  const say = (s, who, t) => s.log.push({ who, t });
  const distracted = s => DISTRACT.includes(s.tick);

  function checkContradiction(s) {
    if (s.knowT && s.knowB) {
      note(s, "differ");
      if (!s.objective) s.objective = "The lesson and your book disagree about the canal. Work out what to answer before the master asks.";
    }
  }

  function advance(s) {
    if (s.crank) {
      const old = s.hopper === "1876" && s.tick === CANAL;
      const line = old ? OLD_CANAL : PAGES[s.tick];
      if (old) { s.classHeardOld = true; note(s, "hopper"); }
      if (s.cap && s.loc === "seat") {
        say(s, "wire", line);
        if (s.tick === CANAL && !old) { s.heardCanal = true; s.knowT = true; }
      }
      s.tick++;
    } else {
      s.crank = true; s.patience--;
      say(s, "master", "Émile! The crank.");
    }
    if (distracted(s)) say(s, "room", "The master turns his back to write the date on the board.");
    checkContradiction(s);
    if (s.patience <= 0 && s.phase === "lesson") {
      s.phase = "recite"; say(s, "master", "Since you have so much to say. Stand. When was the canal of Saint-Aubin opened, and who built it?");
    } else if (s.tick >= MAX && s.phase === "lesson") {
      s.phase = "recite"; say(s, "master", "Caps off. You. When was the canal of Saint-Aubin opened, and who built it?");
    }
  }

  function actions(s) {
    if (s.phase === "recite") {
      const A = [
        { id: "r_trans", label: "Recite the lesson's sentence", ok: s.knowT, why: "You did not hear it, and nobody told you." },
        { id: "r_book", label: "Recite your book", ok: s.knowB, why: "You have not read it." },
        { id: "r_both", label: "Give both, and name the editions", ok: s.knowB && s.knowT && s.notes.includes("edition"), why: "You need both texts and the edition years." },
        { id: "r_ask", label: "Answer with a question: who dug it?", ok: true }
      ];
      if (s.fed && s.emileBlamed === null) A.push({ id: "r_claim", label: "Say you fed the book, not Émile", ok: true });
      return A;
    }
    if (s.phase === "end") return [];
    const atM = s.loc === "machine";
    return [
      { id: "listen", label: atM ? "Wait by the machine" : "Listen", ok: true },
      { id: "cap", label: s.cap ? "Take off the cap" : "Put the cap back on", ok: !atM, why: "There is no cap at the machine." },
      { id: "read", label: "Read the book in your desk", ok: !atM && !s.knowB, why: atM ? "Your book is at your desk." : "Already read." },
      { id: "ask", label: "Raise your hand, ask the master", ok: !atM, why: "Go back to your seat first." },
      { id: "lucie", label: "Whisper to Lucie", ok: !atM, why: "She is at her desk." },
      { id: "show", label: "Show Lucie your book", ok: !atM && s.knowB && s.lucie >= 1, why: "Talk to her first, and read it yourself." },
      { id: "say", label: "Say it out loud to the class", ok: !atM && s.knowB, why: "You have nothing to say yet." },
      { id: "go", label: atM ? "Go back to your seat" : "Walk to the machine", ok: true },
      { id: "hopper", label: "Look into the hopper", ok: atM, why: "It is at the front." },
      { id: "shelf", label: "Look at the shelf", ok: atM, why: "It is behind the machine." },
      { id: "emile", label: "Talk to Émile", ok: atM, why: "He is at the crank." },
      { id: "stop", label: "Ask Émile to stop the crank", ok: atM && s.emile >= 1 && s.crank, why: "He doesn't know you yet." },
      { id: "feed", label: "Feed your book into the hopper", ok: atM && s.emile >= 2 && s.knowB && !s.fed && s.tick <= CANAL && distracted(s), why: "You need Émile's help, your book, and the master's back turned before chapter XII is read." }
    ].map(a => ({ ...a, ok: !!a.ok }));
  }

  function act(s0, id) {
    const s = clone(s0);
    const a = actions(s).find(x => x.id === id);
    if (!a || !a.ok) return s0;
    if (s.phase === "recite") return recite(s, id);
    switch (id) {
      case "listen": break;
      case "cap":
        s.cap = !s.cap;
        if (!s.cap) { note(s, "crank"); say(s, "room", "Cap off. The room is loud: the crank grinding, Émile breathing hard."); }
        else say(s, "room", "Cap on. The voice again.");
        break;
      case "read":
        s.knowB = true;
        say(s, "book", "Your desk copy, Édition de 1876, " + BOOK_LINE);
        if (s.cap && s.crank) { note(s, "nowait"); say(s, "room", "The voice kept going while you read. You lost your place in both."); }
        break;
      case "ask":
        s.asked++;
        if (s.asked === 1) { note(s, "depends"); say(s, "master", "Listen, don't talk. The machine only reads what is in the hopper, and I put the right book in the hopper."); }
        else { s.patience--; say(s, "master", s.knowB ? "That old copy is the 1876 edition. We use the 1909." : "I have answered you."); if (s.knowB) note(s, "edition"); }
        break;
      case "lucie":
        s.lucie = Math.max(s.lucie, 1);
        if (s.cap) { s.cap = false; note(s, "crank"); say(s, "room", "You lift your cap to whisper."); }
        if (s.tick > CANAL && s.hopper === "1909") {
          s.knowT = true;
          if (s.heardCanal) { note(s, "same"); say(s, "lucie", "“Opened in 1834, by the engineers of the State. Same as you heard.”"); }
          else say(s, "lucie", "“You missed it? Opened in 1834, by the engineers of the State.”");
        } else if (s.tick > CANAL) say(s, "lucie", "“It said men of the valley. 1832. Isn't that your book?”");
        else say(s, "lucie", "“Shh. It hasn't got to the canal yet.”");
        break;
      case "show":
        if (s.lucie < 2) { s.lucie = 2; note(s, "paper"); say(s, "lucie", "“The machine said it inside my head. Yours is only paper. And it's old.”"); }
        else if (s.notes.includes("edition")) { s.lucie = 3; say(s, "lucie", "“1876 and 1909. Same book, different years. One of them is wrong about the date, and one leaves the men out.”"); }
        else say(s, "lucie", "“I told you. Paper.”");
        break;
      case "say":
        s.patience--; note(s, "noone");
        say(s, "you", "“That's not what my book says!”");
        say(s, "room", s.lucie >= 1 ? "Only Lucie, cap half off, turns. The other caps keep humming." : "The caps keep humming. The master turns.");
        break;
      case "go":
        if (s.loc === "seat") {
          s.loc = "machine"; s.cap = false; note(s, "crank");
          if (!distracted(s)) { s.patience--; say(s, "master", "Where are you going? ... Fine. Stand by the machine, since you're so curious."); }
          else say(s, "room", "You slip up the aisle while the master writes.");
        } else { s.loc = "seat"; s.cap = true; say(s, "room", "Back at your desk. Cap on."); }
        break;
      case "hopper":
        note(s, "edition"); note(s, "depends");
        say(s, "machine", "The feeder turns one page per crank. Title page: Histoire de France, cours moyen, Édition de 1909. " +
          (s.hopper === "1876" ? "It is your 1876 copy now." : "Same author as the copy in your desk."));
        break;
      case "shelf":
        note(s, "shelf");
        say(s, "room", "Top row: Histoire de France, Édition de 1876, three copies, dusty. Lower row: the 1909 edition, twelve copies.");
        break;
      case "emile":
        s.emile++;
        if (s.emile === 1) { note(s, "nevercap"); say(s, "emile", "“Eight till noon. They pay my mother by the morning. I've never had a cap on. I don't know what it says.”"); }
        else if (s.emile === 2) { note(s, "oral"); say(s, "emile", "“The canal? My grandfather dug on it. He said they were still digging in '33, forty days a year, for nothing.”"); }
        else { note(s, "shelf"); say(s, "emile", "“They changed the books a while back. The old ones are up top. If he turns round to the board, I can feed anything. It doesn't care what it reads.”"); }
        break;
      case "stop":
        s.crank = false; note(s, "stop");
        say(s, "emile", "He lets go of the handle.");
        say(s, "room", "The hum dies. Every head comes up at once, stopped on the same word.");
        break;
      case "feed":
        s.fed = true; s.hopper = "1876"; note(s, "edition");
        say(s, "machine", "Émile lifts the 1909 volume out. Your 1876 copy goes in, open at chapter XII.");
        break;
    }
    advance(s);
    return s;
  }

  function recite(s, id) {
    const E = (title, body) => { s.phase = "end"; s.ending = { title, body }; };
    if (id === "r_claim") {
      s.emileBlamed = false;
      say(s, "you", "“I put my book in. Émile only cranked.”");
      say(s, "master", "The master writes your name in the register, not Émile's.");
      return s;
    }
    if (s.fed && s.emileBlamed === null) s.emileBlamed = true;
    const blame = s.fed ? (s.emileBlamed ? " The master finds the 1876 copy in the hopper. Émile is sent home without the morning's pay." : " Your name is in the register for tampering.") : "";
    const oral = s.notes.includes("oral");
    if (s.classHeardOld && id !== "r_ask") {
      E("The class recites your book", "Before you finish, the class answers for you: 1832, the men of the valley. They heard your edition the way they would have heard the other, and they repeat its wrong date with the same confidence." + blame);
      return s;
    }
    if (id === "r_trans") {
      E("Marked right", "“Opened in 1834, by the engineers of the State.” The master marks it right. The date is right." + (s.knowB ? " Your book had it wrong. Your book also named the men who dug it, and the lesson does not." : "") + blame);
    } else if (id === "r_book") {
      if (s.lucie >= 3) E("Two witnesses", "You read page 112. Lucie stands: she saw both title pages. The master marks the date wrong, since the canal opened in 1834. He does not mark the rest wrong. He writes in the register that the two editions disagree about who built it." + blame);
      else E("Marked wrong", "You read page 112. “1832 is wrong. The lesson says 1834.” The master is right about the date. Nobody discusses the men of the valley." + blame);
    } else if (id === "r_both") {
      E("Put to the inspector", "You give both sentences and both years: one edition has the date wrong, the other leaves out who dug it." + (oral ? " You add Émile's grandfather. The master says a crank boy's family is not a source." : "") + " The machine reads one book at a time; the master says the inspector will decide which. Tomorrow's lesson will be his answer." + blame);
      if (oral) note(s, "notsource");
    } else {
      E("A question back", "“Who dug it?” The master answers from the 1909 edition: the engineers. " + (s.notes.includes("nevercap") ? "Émile, at the crank, does not look up." : "Nobody asks again.") + blame);
    }
    return s;
  }

  const API = { init, actions, act, NOTES, ASSUMPTIONS, PAGES, MAX, CANAL, BOOK_LINE, DISTRACT };
  if (typeof module !== "undefined") module.exports = API; else root.SCHOOL2000 = API;
})(this);
