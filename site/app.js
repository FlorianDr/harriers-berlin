/* Berlin Harriers — next-run display.
   Stores nothing, reads nothing from the device, makes no network requests.
   The schedule is fully present in the HTML; this only adds a highlight
   and, on a run page, the date of that run's next occurrence. The race
   calendar is complete in the HTML too; this only places the "Upcoming
   races" marker and scrolls the list to it. */
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

/* Race calendar: mark where today falls in the oldest-first list, then scroll
   the list (never the page, so no scrollIntoView) to show that spot. */
(() => {
  "use strict";
  const list = document.querySelector(".season .races");
  if (!list) return;
  const races = [...list.querySelectorAll("[data-race]")];

  // Today in Berlin as YYYY-MM-DD; ISO dates compare correctly as strings.
  const today = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Europe/Berlin", year: "numeric", month: "2-digit", day: "2-digit"
  }).format(new Date());

  // A race still counts as upcoming on its last day.
  const next = races.find(r => r.dataset.race >= today);
  if (next) {
    const marker = document.createElement("div");
    marker.className = "now";
    marker.textContent = "Upcoming races";
    next.before(marker);
    races.slice(races.indexOf(next)).forEach(r => {
      r.classList.add("up");
      if (r.querySelector(".rs")) return;
      const status = document.createElement("span");
      status.className = "rs";
      status.textContent = "upcoming";
      r.append(status);
    });
  }

  // Open at the bottom: the latest races, then what's coming up.
  list.scrollTop = list.scrollHeight;
})();
