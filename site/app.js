/* Berlin Harriers — next-run display and past/upcoming races.
   Stores nothing, reads nothing from the device, makes no network requests.
   The schedule is fully present in the HTML; this only adds a highlight
   and, on a run page, the date of that run's next occurrence. Races that
   are over move from the upcoming list to the past one. */
(() => {
  "use strict";
  const past = document.querySelector(".season .past");
  if (!past) return;

  // Today in Berlin as YYYY-MM-DD, so dates compare as plain strings.
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Europe/Berlin", year: "numeric", month: "2-digit", day: "2-digit"
  }).formatToParts(new Date());
  const get = t => parts.find(p => p.type === t).value;
  const today = `${get("year")}-${get("month")}-${get("day")}`;

  // Oldest first, each to the top: the past list stays newest first.
  // A race counts as past from the day after it ends.
  [...document.querySelectorAll(".season .row.up[data-ends]")]
    .filter(row => row.dataset.ends < today)
    .sort((a, b) => a.dataset.ends.localeCompare(b.dataset.ends))
    .forEach(row => {
      row.classList.remove("up");
      past.prepend(row);
    });

  if (!document.querySelector(".season .row.up")) {
    document.querySelector(".season .now").hidden = true;
  }
})();

(() => {
  "use strict";
  const rows = [...document.querySelectorAll("[data-day]")];
  if (!rows.length) return;

  // Berlin time, regardless of where the reader is.
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Europe/Berlin", weekday: "short", hour: "2-digit",
    minute: "2-digit", hour12: false
  }).formatToParts(new Date());
  const get = t => parts.find(p => p.type === t).value;
  const DAYS = { Sun:0, Mon:1, Tue:2, Wed:3, Thu:4, Fri:5, Sat:6 };
  const nowDay = DAYS[get("weekday")];
  const nowMin = (+get("hour")) * 60 + (+get("minute"));

  // Minutes from now until each run's next occurrence.
  let best = null;
  for (const el of rows) {
    const day = +el.dataset.day;
    const [h, m] = el.dataset.time.split(":").map(Number);
    let delta = ((day - nowDay + 7) % 7) * 1440 + (h * 60 + m) - nowMin;
    if (delta < 0) delta += 7 * 1440;          // already gone today → next week
    if (!best || delta < best.delta) best = { el, delta };
  }
  if (!best) return;

  best.el.classList.add("today");

  const d = best.el.dataset;
  const band = document.getElementById("next-run");
  if (band) {
    band.querySelector("[data-next-when]").textContent = `${d.label} ${d.time}`;
    band.querySelector("[data-next-where]").textContent = d.where;
  }
  // Point every next-run link at that run's own page.
  const page = best.el.querySelector(".name a");
  if (page) document.querySelectorAll("[data-next-link]").forEach(link => {
    link.href = page.getAttribute("href");
  });
  // "See you on Tuesday." — and "today" when the run is still to come today.
  const isToday = +d.day === nowDay && best.delta < 1440;
  document.querySelectorAll("[data-next-day]").forEach(el => {
    el.textContent = isToday ? "today" : d.label;
  });
  // "The next one is Tuesday Track today at 19:15."
  const name = best.el.querySelector(".name a");
  if (name) document.querySelectorAll("[data-next-run]").forEach(el => {
    el.textContent = `${name.textContent} ${isToday ? "today" : `on ${d.label}`} at ${d.time}`;
  });

  // Run pages: the calendar date of that run's next occurrence.
  const dateEls = document.querySelectorAll("[data-next-date]");
  if (dateEls.length) {
    const when = new Date(Date.now() + best.delta * 60000);
    const fmt = opts => new Intl.DateTimeFormat("en-GB",
      { timeZone: "Europe/Berlin", day: "numeric", month: "long", ...opts }).format(when);
    const text = isToday ? `Today, ${fmt({})}` : fmt({ weekday: "long" });
    dateEls.forEach(el => { el.textContent = text; });
  }

  // Carousel: land on the next run without moving the page.
  const track = document.querySelector(".fixtures");
  if (track && getComputedStyle(track).overflowX !== "visible") {
    track.scrollLeft = best.el.offsetLeft - track.offsetLeft;
  }
})();
