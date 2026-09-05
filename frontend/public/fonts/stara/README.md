# Stara (titles)

Stara is a licensed geometric sans. The CSS stack is `Stara, Quicksand, Helvetica Neue`.

If Stara is installed on the computer, titles use it. Otherwise they use the self-hosted Quicksand files in `public/fonts/quicksand`.

To ship the real webfont, drop licensed `.woff2` files here and add `@font-face` `url()` rules in `src/index.css`. Do not add empty `local()` faces — browsers will treat Stara as loaded and fall back to Times.
