---
name: reference-spotlistr-bulk-playlist
description: How to bulk-build a Spotify playlist from a text song list via Spotlistr + the gotchas that cost us time
metadata: 
  node_type: memory
  type: reference
  originSessionId: d727975c-6519-4094-b6db-e14daaac7fa0
---

Tool: **spotlistr.com/search/textbox/spotify** — paste "Title - Artist" lines (one per song), Search, then "Create Playlist". Uses Spotlistr's OWN Spotify creds, so it is NOT subject to the rate-limit that hits a captured web-player token. Preserves paste order exactly. Free; "create playlist" makes a NEW playlist only (no add-to-existing).

Driving it via chrome-devtools-mcp: the input is a React controlled textarea — the `fill` tool's value gets reverted on submit. Set it with the native setter instead:
`Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(ta,text)` then dispatch `input`+`change` events. Results render with `content-visibility:auto`, so read selected cards via `textContent` (not `innerText`, which is empty off-screen); the chosen card has `aria-pressed="true"`, candidate album/artist is in its text and the img `alt="Album cover for X by Y"`.

Key insight when a scrape has WRONG artists (e.g. cover-art mislabels): searching `Title + wrongArtist` returns junk. Searching **title-only** lets Spotify popularity pick the real hit — fixes most mislabels. For generic titles (Solo, Love Me, Suicide, Daylight, Sticky) title-only collides, so you still need the true artist. The user's [[project-top-tracks-2024-playlist]] source was stats.fm screenshots; album cover art was the ground-truth for recovering true artists.

Spotify Web API search via a captured `Bearer` token (hook `window.fetch`/`XHR.setRequestHeader` on open.spotify.com, reload with initScript) is heavily rate-limited (retry-after 35-55s) when another session is also hitting it — see [[reference-chrome-devtools-live-browser]]. Two chats sharing one live Chrome collide and even close each other's tabs.
