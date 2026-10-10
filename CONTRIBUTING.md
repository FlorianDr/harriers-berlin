# Contributing

Thanks for helping. A few things make a change easy to accept.

## Before you start

Read [AGENTS.md](AGENTS.md) — despite the name it is the shortest accurate description of how the
site is built and which rules are easy to break.

## The rules that matter most

1. **Nothing that talks to a third party.** No CDN, web fonts from Google, embedded maps,
   Instagram/YouTube embeds or analytics. The privacy policy promises this and it is why the site
   needs no cookie banner. Link out instead.
2. **No storage.** No cookies, `localStorage` or `sessionStorage`.
3. **The page must work with JavaScript off.** Scripts may enhance; content lives in the HTML.
4. **Check contrast.** Keep text at WCAG AA or better. Volt in particular fails on white.
5. **Keep the voice.** Dry, specific, friendly. No hype, no exclamation marks, no emoji in prose.

If a change touches what the site collects, loads or stores, the Datenschutzerklärung in
`site/impressum.html` probably needs updating too — say so in the pull request.

## Most wanted

- **Real photos** from club runs, with the consent of everyone recognisable in them.
- **GPX exports** of the four regular routes, to replace the indicative route shapes.
- **Real race results** for the season record.

## Testing a change

There is no build or test suite. Serve `site/` locally, then check:

- light and dark mode
- a narrow phone width (the schedule becomes a swipeable carousel below 46rem)
- keyboard navigation and visible focus
- JavaScript disabled
- `prefers-reduced-motion`

## Personal data

This repository is public. Don't add names, photos or contact details of members beyond what the
Impressum legally requires, unless the person has agreed.
