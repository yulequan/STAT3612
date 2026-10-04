// The entry page fixes its base before history navigation changes the pathname.
// SSR loads the same catalog when generating static route entries.
export const siteBase = import.meta.env.SSR
  ? '/'
  : new URL(import.meta.env.BASE_URL, document.baseURI).pathname

export function courseHref(path = ''): string {
  return `${siteBase}${path.replace(/^\//, '')}`
}

export function readPath(): string {
  const path = window.location.pathname
    .slice(siteBase.length)
    .replace(/(?:^|\/)index\.html$/, '')
    .replace(/\/$/, '')
  const canonical = courseHref(path)
  if (window.location.pathname !== canonical)
    window.history.replaceState(null, '', canonical + window.location.search + window.location.hash)
  return path
}

export function navigateCourse(event: MouseEvent): boolean {
  if (
    event.defaultPrevented ||
    event.button !== 0 ||
    event.metaKey ||
    event.ctrlKey ||
    event.shiftKey ||
    event.altKey
  )
    return false
  const link = (event.target as Element).closest<HTMLAnchorElement>('a[href]')
  if (!link || link.hasAttribute('download') || (link.target && link.target !== '_self'))
    return false
  const url = new URL(link.href)
  if (
    url.origin !== window.location.origin ||
    !url.pathname.startsWith(siteBase) ||
    url.hash ||
    /\.[^/]+$/.test(url.pathname)
  )
    return false
  event.preventDefault()
  if (url.href !== window.location.href) window.history.pushState(null, '', url.href)
  return true
}
