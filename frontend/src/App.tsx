import { type ChangeEvent, type FormEvent, type MouseEvent, type ReactNode, useEffect, useRef, useState } from 'react'
import './App.css'

type Page = 'chat' | 'campaigns' | 'knowledge' | 'integrations' | 'settings' | 'campaign-chat' | 'overview' | 'audience' | 'strategy' | 'launch'
type AuthMode = 'login' | 'signup'
type UserSettings = { name: string; workspace: string; digest_enabled: boolean; permission_policy: 'ask' | 'auto' }
type IconName = 'activity' | 'arrow' | 'brief' | 'campaigns' | 'chevron' | 'creative' | 'dots' | 'insights' | 'plus' | 'search' | 'settings' | 'spark' | 'strategy' | 'trend' | 'send' | 'lock' | 'check' | 'play' | 'book' | 'collapse' | 'external' | 'plug' | 'file' | 'eye' | 'eyeOff' | 'logout' | 'user'

const API_URL = import.meta.env.VITE_API_URL ?? (import.meta.env.PROD ? 'https://kloppy.onrender.com/api' : 'http://localhost:8000/api')

const navItems: { label: string; page: Page; icon: IconName }[] = [
  { label: 'Kloppy', page: 'chat', icon: 'spark' },
  { label: 'Campaigns', page: 'campaigns', icon: 'campaigns' },
  { label: 'Knowledge', page: 'knowledge', icon: 'book' },
  { label: 'Integrations', page: 'integrations', icon: 'plug' },
  { label: 'Settings', page: 'settings', icon: 'settings' },
]

const campaignNav: { label: string; page: Page; icon: IconName }[] = [
  { label: 'Kloppy', page: 'campaign-chat', icon: 'spark' },
  { label: 'Overview', page: 'overview', icon: 'activity' },
  { label: 'Audience', page: 'audience', icon: 'insights' },
  { label: 'Strategy', page: 'strategy', icon: 'strategy' },
  { label: 'Launch & learn', page: 'launch', icon: 'trend' },
]

type IntegrationItem = { id: string; name: string; kind: string; category: string; description: string; status: string; connected: boolean; server_url?: string | null; allowed_tools?: string[] }
type KnowledgeSource = { id: string; title: string; content: string; source_type: 'brand_text' | 'document'; file_name?: string | null; created_at: string }

function Icon({ name, size = 18 }: { name: IconName; size?: number }) {
  const common = { width: size, height: size, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 1.8, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const, 'aria-hidden': true }
  const paths: Record<IconName, ReactNode> = {
    activity: <path d="M3 12h4l2.1-6 4.2 12 2.1-6H21" />,
    campaigns: <><path d="M4 5.5h16v13H4z" /><path d="M8 9h8M8 13h5M8 17h3" /></>,
    insights: <><circle cx="11" cy="11" r="6.5" /><path d="m16 16 4.5 4.5M8.5 11h5M11 8.5v5" /></>,
    creative: <><path d="m5 19 1.3-4.7L16.8 3.8a2.1 2.1 0 0 1 3 3L9.3 17.3 5 19Z" /><path d="m14.5 6.1 3.4 3.4" /></>,
    strategy: <><path d="M4 19V5M4 19h16" /><path d="m7 15 3-4 3 2 5-6" /></>,
    settings: <><path d="M12 8.2a3.8 3.8 0 1 0 0 7.6 3.8 3.8 0 0 0 0-7.6Z" /><path d="m19.3 13.5 1.2.9-1.5 2.6-1.4-.5a7.8 7.8 0 0 1-1.5.9l-.2 1.5h-3l-.3-1.5a7.8 7.8 0 0 1-1.5-.9l-1.4.5-1.5-2.6 1.2-.9a6.5 6.5 0 0 1 0-1.8l-1.2-.9 1.5-2.6 1.4.5a7.8 7.8 0 0 1 1.5-.9l.3-1.5h3l.2 1.5a7.8 7.8 0 0 1 1.5.9l1.4-.5 1.5 2.6-1.2.9a6.5 6.5 0 0 1 0 1.8Z" /></>,
    brief: <><path d="M6 4.5h12v15H6zM9 8h6M9 12h6M9 16h3" /></>,
    spark: <path d="m12 3 1.6 6.4L20 11l-6.4 1.6L12 19l-1.6-6.4L4 11l6.4-1.6L12 3Z" />,
    trend: <><path d="M4 16.5 9 12l3 2.5L20 6" /><path d="M15 6h5v5" /></>,
    plus: <><path d="M12 5v14M5 12h14" /></>,
    search: <><circle cx="10.8" cy="10.8" r="6.3" /><path d="m16 16 4.2 4.2" /></>,
    arrow: <><path d="M5 12h13M13 7l5 5-5 5" /></>,
    chevron: <path d="m8 10 4 4 4-4" />,
    dots: <><circle cx="5" cy="12" r="1" fill="currentColor" stroke="none" /><circle cx="12" cy="12" r="1" fill="currentColor" stroke="none" /><circle cx="19" cy="12" r="1" fill="currentColor" stroke="none" /></>,
    send: <><path d="m4 4 16 8-16 8 3-8-3-8Z" /><path d="M7 12h13" /></>,
    lock: <><rect x="5" y="10" width="14" height="10" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></>,
    check: <path d="m5 12 4 4L19 6" />,
    play: <path d="m9 6 9 6-9 6V6Z" />,
    book: <><path d="M5 5.5A2.5 2.5 0 0 1 7.5 3H20v16H7.5A2.5 2.5 0 0 0 5 21.5z" /><path d="M5 5.5v16M8 7h8M8 11h8" /></>,
    collapse: <><path d="m15 6-6 6 6 6" /><path d="M9 12h10" /></>,
    external: <><path d="M14 5h5v5M19 5l-8 8" /><path d="M18 13v5a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5" /></>,
    plug: <><path d="M8 12V5M16 12V5M5 9h14M12 9v5a4 4 0 0 1-8 0M12 14a4 4 0 0 0 8 0V9" /></>,
    file: <><path d="M6 3.5h8l4 4V20.5H6z" /><path d="M14 3.5v4h4M9 12h6M9 16h4" /></>,
    eye: <><path d="M2.5 12s3.2-6 9.5-6 9.5 6 9.5 6-3.2 6-9.5 6-9.5-6-9.5-6Z" /><circle cx="12" cy="12" r="2.5" /></>,
    eyeOff: <><path d="m3 3 18 18M10.6 6.2A10.8 10.8 0 0 1 12 6c6.3 0 9.5 6 9.5 6a15.6 15.6 0 0 1-3 3.6M6.2 6.2C3.8 7.7 2.5 12 2.5 12s3.2 6 9.5 6c.8 0 1.6-.1 2.3-.3" /><path d="M9.9 9.9a3 3 0 0 0 4.2 4.2" /></>,
    logout: <><path d="M10 17l5-5-5-5M15 12H3" /><path d="M12 3h6a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-6" /></>,
    user: <><circle cx="12" cy="8" r="3.4" /><path d="M5 20a7 7 0 0 1 14 0" /></>,
  }
  return <svg {...common}>{paths[name]}</svg>
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem('kloppy-session')
  const headers = new Headers(options?.headers)
  headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(`${API_URL}${path}`, { ...options, headers })
  if (!response.ok) {
    const body = await response.json().catch(() => ({})) as { detail?: string }
    throw new Error(body.detail ?? 'Request failed')
  }
  if (response.status === 204) return undefined as T
  return response.json()
}

async function uploadRequest<T>(path: string, data: FormData): Promise<T> {
  const headers = new Headers()
  const token = localStorage.getItem('kloppy-session')
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(`${API_URL}${path}`, { method: 'POST', headers, body: data })
  if (!response.ok) {
    const body = await response.json().catch(() => ({})) as { detail?: string }
    throw new Error(body.detail ?? 'Upload failed')
  }
  return response.json()
}

function Brand() {
  return <div className="brand-lockup"><span className="brand-k">k</span><span className="brand-name">kloppy</span></div>
}

function KloppyMark({ size = 'small' }: { size?: 'small' | 'large' }) {
  return <span className={`kloppy-mark ${size}`} aria-label="Kloppy"><span className="brand-k">k</span></span>
}

function formatInline(text: string): ReactNode[] {
  const normalized = text.replace(/\\([*_~`#[\]])/g, '$1')
  const tokens = /(\*\*[^*]+\*\*|__[^_]+__|~~[^~]+~~|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\(https?:\/\/[^\s)]+\))/g
  return normalized.split(tokens).filter(Boolean).map((part, index) => {
    if (part.startsWith('**') || part.startsWith('__')) return <strong key={index}>{part.slice(2, -2)}</strong>
    if (part.startsWith('~~')) return <del key={index}>{part.slice(2, -2)}</del>
    if (part.startsWith('*')) return <em key={index}>{part.slice(1, -1)}</em>
    if (part.startsWith('`')) return <code key={index}>{part.slice(1, -1)}</code>
    const link = part.match(/^\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)$/)
    if (link) return <a key={index} href={link[2]} target="_blank" rel="noreferrer">{link[1]}</a>
    return part
  })
}

function FormattedText({ text }: { text: string }) {
  const blocks: ReactNode[] = []
  const paragraph: string[] = []
  const lines = text.replace(/\\([*_~`#[\]])/g, '$1').split(/\r?\n/)
  const flushParagraph = () => {
    if (!paragraph.length) return
    blocks.push(<p key={`p-${blocks.length}`}>{formatInline(paragraph.join(' '))}</p>)
    paragraph.length = 0
  }

  for (let index = 0; index < lines.length;) {
    const line = lines[index]
    if (!line.trim()) { flushParagraph(); index += 1; continue }

    const heading = line.match(/^\s{0,3}(#{1,3})\s+(.+)$/)
    if (heading) {
      flushParagraph()
      const Tag = `h${heading[1].length + 1}` as 'h2' | 'h3' | 'h4'
      blocks.push(<Tag key={`h-${index}`}>{formatInline(heading[2].replace(/\s+#+\s*$/, ''))}</Tag>)
      index += 1
      continue
    }

    const listItem = line.match(/^\s*(?:[-*+]\s+|\d+[.)]\s+)(.+)$/)
    if (listItem) {
      flushParagraph()
      const ordered = /^\s*\d+[.)]\s+/.test(line)
      const items: string[] = []
      while (index < lines.length) {
        const match = lines[index].match(/^\s*(?:[-*+]\s+|\d+[.)]\s+)(.+)$/)
        if (!match || /^\s*\d+[.)]\s+/.test(lines[index]) !== ordered) break
        items.push(match[1]); index += 1
      }
      const List = ordered ? 'ol' : 'ul'
      blocks.push(<List key={`list-${index}`}>{items.map((item, itemIndex) => <li key={itemIndex}>{formatInline(item)}</li>)}</List>)
      continue
    }

    if (/^\s*```/.test(line)) {
      flushParagraph()
      const code: string[] = []
      index += 1
      while (index < lines.length && !/^\s*```/.test(lines[index])) code.push(lines[index++])
      if (index < lines.length) index += 1
      blocks.push(<pre key={`code-${index}`}><code>{code.join('\n')}</code></pre>)
      continue
    }

    paragraph.push(line.trim())
    index += 1
  }
  flushParagraph()
  return <div className="formatted-text">{blocks}</div>
}

function Landing({ onAuth }: { onAuth: (mode: AuthMode) => void }) {
  const scrollToSection = (event: MouseEvent<HTMLAnchorElement>, id: string) => {
    event.preventDefault()
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    window.history.replaceState(null, '', `#landing-${id}`)
  }
  return <div className="public-page">
    <header className="public-nav"><Brand /><nav className="public-links"><a href="#problem" onClick={(event) => scrollToSection(event, 'problem')}>The problem</a><a href="#method" onClick={(event) => scrollToSection(event, 'method')}>How it works</a><a href="#control" onClick={(event) => scrollToSection(event, 'control')}>Trust</a><button className="button secondary" onClick={() => onAuth('login')}>Sign in</button><button className="button primary" onClick={() => onAuth('signup')}>Start a campaign <Icon name="arrow" size={15} /></button></nav></header>
    <main>
      <section className="landing-hero"><div className="hero-copy"><span className="eyebrow">For teams who are done stitching it together</span><h1>Marketing gets messy when every decision lives <em>somewhere else.</em></h1><p>You have a brief in one place, research in another, a strategy deck nobody is reading, and creative waiting for context. Kloppy gives your team one intelligent place to move from the first question to the work that ships.</p><div className="hero-actions"><button className="button primary large" onClick={() => onAuth('signup')}>See your next best move <Icon name="arrow" size={17} /></button><span className="hero-note"><Icon name="check" size={14} /> Built for the whole campaign</span></div></div><div className="agent-preview"><div className="preview-top"><span className="live-dot" /> Kloppy campaign <span>ready when you are</span></div><div className="preview-message"><div className="agent-avatar">K</div><div><strong>Start with what you know.</strong><p>“We’re launching a product for independent teams. We need a sharper audience and a campaign people can recognize themselves in.”</p></div></div><div className="preview-response"><span className="response-line" /><div><strong>Here’s where I’d begin.</strong><p>Read the audience signal, test the strategic direction, then turn the approved idea into a coordinated campaign.</p></div></div><div className="preview-input">Ask Kloppy to find the next move <Icon name="send" size={16} /></div></div></section>
      <section className="landing-problem" id="problem"><div className="section-lead"><span className="eyebrow">The cost of disconnected marketing</span><h2>Your team shouldn’t need to become the system.</h2><p>Good people lose time translating between tools, repeating context, and debating decisions that should already be connected.</p></div><div className="problem-list"><div><strong>01</strong><h3>Insight gets stranded</h3><p>Research becomes a document instead of a useful decision about who to reach and why.</p></div><div><strong>02</strong><h3>Strategy loses its thread</h3><p>The brief, audience, message, and channels drift apart as more people touch the work.</p></div><div><strong>03</strong><h3>Creative starts from scratch</h3><p>Every asset request becomes another round of explaining what the campaign is supposed to mean.</p></div><div><strong>04</strong><h3>Learning arrives too late</h3><p>Performance tells you what happened, but not what the next move should be.</p></div></div></section>
      <section className="landing-method" id="method"><div className="section-lead"><span className="eyebrow">The Kloppy method</span><h2>One campaign context.<br />Every layer connected.</h2><p>Talk to Kloppy like a marketing officer who knows the brief, keeps the evidence close, and helps your team make the next decision.</p></div><div className="method-steps"><div className="method-step featured"><span>01</span><div><Icon name="insights" size={20} /><h3>Understand the market</h3><p>Turn a product brief into audience directions, cultural signals, and clear confidence levels.</p></div></div><div className="method-step"><span>02</span><div><Icon name="strategy" size={20} /><h3>Decide with context</h3><p>Challenge the positioning, sharpen the message, and see the reasoning behind the recommendation.</p></div></div><div className="method-step"><span>03</span><div><Icon name="creative" size={20} /><h3>Make the campaign</h3><p>Move from an approved strategy to a coherent set of stories, assets, and channel-ready work.</p></div></div><div className="method-step"><span>04</span><div><Icon name="trend" size={20} /><h3>Learn what to do next</h3><p>Bring results back into the conversation so the next campaign starts smarter.</p></div></div></div></section>
      <section className="landing-campaign"><div><span className="eyebrow">From conversation to campaign</span><h2>Not a collection of outputs.<br /><em>A line of sight.</em></h2></div><div className="campaign-route"><div><span className="route-dot coral" /><strong>Brief</strong><p>What are we trying to make true?</p></div><div><span className="route-dot mint" /><strong>Audience</strong><p>Who should feel this first?</p></div><div><span className="route-dot gold" /><strong>Strategy</strong><p>What should we say and why?</p></div><div><span className="route-dot navy" /><strong>Creative</strong><p>How does the idea travel?</p></div><div><span className="route-dot coral" /><strong>Launch</strong><p>What is ready to authorize?</p></div></div></section>
      <section className="landing-control" id="control"><div className="control-copy"><span className="eyebrow">Designed for responsible action</span><h2>Move quickly.<br />Stay in control.</h2><p>Kloppy can recommend, draft, compare, and coordinate. Your team still owns the decisions that matter.</p></div><div className="control-list"><div><Icon name="check" size={17} /><span><strong>Evidence stays visible</strong><small>Separate what is known, inferred, and still worth testing.</small></span></div><div><Icon name="check" size={17} /><span><strong>Approvals stay human</strong><small>Nothing consequential is published, spent, or changed without your say.</small></span></div><div><Icon name="check" size={17} /><span><strong>Context stays yours</strong><small>Keep the brief, decisions, assets, and learnings together in Kloppy.</small></span></div></div></section>
      <section className="landing-cta"><span className="eyebrow">Your next campaign can start here</span><h2>Bring the question.<br /><em>Leave with a direction.</em></h2><p>Start with the product, the launch, or the problem your team is trying to solve.</p><button className="button primary large" onClick={() => onAuth('signup')}>Start a campaign <Icon name="arrow" size={17} /></button></section>
    </main>
    <footer className="public-footer"><Brand /><span>Kloppy · An AI marketing officer for teams who want the work to connect.</span><button onClick={() => onAuth('login')}>Sign in <Icon name="arrow" size={14} /></button></footer>
  </div>
}

function Auth({ mode, onMode, onComplete }: { mode: AuthMode; onMode: (mode: AuthMode) => void; onComplete: (user: { name: string }) => void }) {
  const [email, setEmail] = useState(''); const [password, setPassword] = useState(''); const [name, setName] = useState(''); const [error, setError] = useState(''); const [notice, setNotice] = useState(''); const [showPassword, setShowPassword] = useState(false); const [busy, setBusy] = useState(false)
  const submit = async (event: FormEvent) => { event.preventDefault(); setBusy(true); setError(''); setNotice(''); try { const data = await request<{ token: string | null; message?: string | null; user: { name: string; email?: string | null } }>(`/auth/${mode === 'login' ? 'login' : 'signup'}`, { method: 'POST', body: JSON.stringify({ email, password, name: mode === 'signup' ? name : undefined }) }); if (mode === 'signup') { setPassword(''); setNotice(data.token ? 'Your account is ready. Sign in with your email and password.' : data.message ?? 'Your account was created. Check your email to complete signup.'); onMode('login'); return } if (!data.token) { setNotice(data.message ?? 'Sign in to continue.'); return } localStorage.setItem('kloppy-session', data.token); onComplete({ name: data.user.name }) } catch (err) { setError(err instanceof Error ? err.message : 'Unable to continue. Try again.') } finally { setBusy(false) } }
  return <div className="auth-page"><div className="auth-aside"><Brand /><div><span className="eyebrow">The campaign co-pilot</span><h1>Good marketing starts with a better read.</h1><p>Bring the brief. Kloppy will help you find the signal, make the decision, and turn it into work.</p></div><span className="auth-foot">Evidence-aware by design.</span></div><div className="auth-card-wrap"><div className="auth-card"><div className="auth-heading"><span className="eyebrow">{mode === 'login' ? 'Welcome back' : 'Start with the brief'}</span><h2>{mode === 'login' ? 'Sign in to your Kloppy account.' : 'Create your Kloppy account.'}</h2><p>{mode === 'login' ? 'Pick up where your next best move is waiting.' : 'Your campaign context stays connected from insight to action.'}</p></div><form onSubmit={submit}>{mode === 'signup' && <label>Name<input value={name} onChange={(e) => setName(e.target.value)} placeholder="Amara K." required /></label>}<label>Work email<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@company.com" required /></label><label>Password<span className="password-input"><input type={showPassword ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="8 characters minimum" minLength={8} required /><button type="button" className="password-visibility" aria-label={showPassword ? 'Hide password' : 'Show password'} aria-pressed={showPassword} onClick={() => setShowPassword(!showPassword)}><Icon name={showPassword ? 'eyeOff' : 'eye'} size={17} /></button></span></label>{error && <p className="form-error" role="alert">{error}</p>}{notice && <p className="form-notice" role="status">{notice}</p>}<button className="button primary full" disabled={busy}>{busy ? 'Opening Kloppy…' : mode === 'login' ? 'Open Kloppy' : 'Create account'} <Icon name="arrow" size={16} /></button></form><div className="auth-switch">{mode === 'login' ? 'New to Kloppy?' : 'Already have an account?'} <button onClick={() => onMode(mode === 'login' ? 'signup' : 'login')}>{mode === 'login' ? 'Create one' : 'Sign in'}</button></div><p className="secure-note"><Icon name="lock" size={13} /> Your account is private by default.</p></div></div></div>
}

function Sidebar({ page, setPage, user, onLogout }: { page: Page; setPage: (page: Page) => void; user: { name: string }; onLogout: () => void }) {
  const [collapsed, setCollapsed] = useState(false)
  return <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}><div className="sidebar-top"><Brand /><button className="sidebar-toggle" aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'} onClick={() => setCollapsed(!collapsed)}><Icon name="collapse" size={17} /></button></div><nav className="main-nav" aria-label="Main navigation">{navItems.filter((item) => item.page !== 'settings').map((item) => <button title={collapsed ? item.label : undefined} aria-label={item.label} className={`nav-item ${page === item.page ? 'active' : ''}`} key={item.page} onClick={() => setPage(item.page)}>{item.page === 'chat' ? <KloppyMark /> : <Icon name={item.icon} />}<span>{item.label}</span></button>)}</nav><div className="sidebar-bottom"><button className={`nav-item settings-nav ${page === 'settings' ? 'active' : ''}`} onClick={() => setPage('settings')}><Icon name="settings" /><span>Settings</span></button><div className="user-profile"><button className={`user-avatar profile-button ${page === 'settings' ? 'active' : ''}`} type="button" title={`${user.name} · Profile settings`} aria-label={`Open ${user.name} profile settings`} aria-current={page === 'settings' ? 'page' : undefined} onClick={() => setPage('settings')}><Icon name="user" size={17} /></button><button className="logout-button" type="button" title="Log out" aria-label="Log out" onClick={onLogout}><Icon name="logout" size={16} /><span>Log out</span></button></div></div></aside>
}

type PermissionPolicy = 'ask' | 'auto'
type AgentActivity = { label: string; status: string; tool?: string }
type DocumentArtifact = { title: string; content: string; format?: string; filename?: string }
type ChatMessage = { role: 'agent' | 'user'; text: string; artifact?: DocumentArtifact; activities?: AgentActivity[] }
type Campaign = { id: string; name: string; createdAt: string }

function accountKey() {
  const token = localStorage.getItem('kloppy-session') ?? 'anonymous'
  try { return JSON.parse(atob(token.split('.')[1])).sub ?? 'account' } catch { return token.slice(0, 24) }
}

function readCampaigns(): Campaign[] {
  try { return JSON.parse(localStorage.getItem(`kloppy-campaigns:${accountKey()}`) ?? '[]') as Campaign[] } catch { return [] }
}

function ActivityFeed({ events, live = false }: { events: AgentActivity[]; live?: boolean }) {
  if (!events.length) return null
  return <section className={`activity-feed ${live ? 'live' : ''}`} aria-label={live ? 'Kloppy activity' : 'Completed activity'} aria-live={live ? 'polite' : undefined}>
    <div className="activity-feed-head"><Icon name="activity" size={13} /><span>{live ? 'Working on your request' : 'What Kloppy did'}</span></div>
    <ol>{events.map((event, index) => <li className={event.status === 'done' ? 'done' : 'working'} key={`${event.label}-${event.status}-${index}`}><span className="activity-state"><Icon name={event.status === 'done' ? 'check' : 'activity'} size={12} /></span><span>{event.label}</span></li>)}</ol>
  </section>
}

function Assistant({ fullPage = false, campaignId, campaignName, onSpinOffCampaign }: { fullPage?: boolean; campaignId?: string; campaignName?: string; onSpinOffCampaign?: (name: string, messages: ChatMessage[]) => void }) {
  const historyKey = campaignId ? `kloppy-chat:${accountKey()}:${campaignId}` : null
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    if (historyKey) { try { const saved = localStorage.getItem(historyKey); if (saved) return JSON.parse(saved) as ChatMessage[] } catch { /* recover with a fresh conversation */ } }
    return []
  })
  const [input, setInput] = useState(() => {
    if (!campaignId) return ''
    const key = `kloppy-next-prompt:${accountKey()}:${campaignId}`
    const prompt = sessionStorage.getItem(key) ?? ''
    sessionStorage.removeItem(key)
    return prompt
  }); const [busy, setBusy] = useState(false); const [permission, setPermission] = useState<PermissionPolicy>('ask')
  const [permissionSaveError, setPermissionSaveError] = useState('')
  const [spinOffOpen, setSpinOffOpen] = useState(false)
  const [spinOffName, setSpinOffName] = useState('')
  const [menuOpen, setMenuOpen] = useState(false); const [files, setFiles] = useState<string[]>([]); const [contextItems, setContextItems] = useState<string[]>([]); const [viewer, setViewer] = useState<ChatMessage['artifact']>(undefined); const [socket, setSocket] = useState<WebSocket | null>(null); const [activities, setActivities] = useState<AgentActivity[]>([])
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => { if (historyKey) localStorage.setItem(historyKey, JSON.stringify(messages)) }, [historyKey, messages])

  useEffect(() => {
    request<UserSettings>('/settings').then((saved) => setPermission(saved.permission_policy)).catch(() => setPermission('ask'))
  }, [])

  useEffect(() => {
    const textarea = inputRef.current
    if (!textarea) return
    textarea.style.height = 'auto'
    textarea.style.height = `${Math.min(textarea.scrollHeight, 150)}px`
    textarea.style.overflowY = 'hidden'
  }, [input])

  useEffect(() => {
    const token = localStorage.getItem('kloppy-session')
    if (!token) return
    const websocketBase = API_URL.replace(/^http/, 'ws').replace(/\/$/, '')
    const connection = new WebSocket(`${websocketBase}/assistant/ws?access_token=${encodeURIComponent(token)}`)
    connection.onmessage = (event) => {
      const data = JSON.parse(event.data) as { type?: string; reply?: string; error?: string; error_code?: string; artifact?: DocumentArtifact; activities?: AgentActivity[]; label?: string; status?: string; tool?: string }
      if (data.type === 'activity') {
        setActivities((items) => [...items, { label: data.label ?? 'Working on your request', status: data.status ?? 'working', tool: data.tool }])
        return
      }
      const lowerError = data.error?.toLowerCase() ?? ''
      const errorMessage = lowerError.includes('schema cache') || lowerError.includes('user_settings')
        ? 'Kloppy can’t read your saved settings yet. Apply backend/db/003_user_settings.sql in Supabase, then retry.'
        : data.error_code === 'authentication_required'
          ? 'Your session has expired. Sign in again to continue.'
          : lowerError.includes('not configured')
        ? 'I’m not connected to my AI service yet. Add OPENROUTER_API_KEY to backend/.env, then restart the API.'
        : data.error ? 'I couldn’t complete that just now. Please try again in a moment.' : undefined
      setMessages((items) => [...items, { role: 'agent', text: data.reply ?? errorMessage ?? 'The agent returned no response.', artifact: data.artifact, activities: data.activities }])
      if (data.artifact) setViewer(data.artifact)
      setActivities([])
      setBusy(false)
    }
    connection.onopen = () => setSocket(connection)
    connection.onclose = () => setSocket(null)
    return () => connection.close()
  }, [])

  const send = async (value = input) => {
    if (!value.trim() || busy) return
    const conversation_history = messages.slice(-16).map((message) => ({
      role: message.role === 'agent' ? 'assistant' as const : 'user' as const,
      content: message.text,
    }))
    const payload = { message: value, attachments: files, context_items: contextItems, conversation_history, campaign_id: campaignId, campaign_name: campaignName }
    setMessages((items) => [...items, { role: 'user', text: value }]); setInput(''); setBusy(true); setActivities([{ label: 'Connecting campaign context and available tools', status: 'working' }])
    if (socket?.readyState === WebSocket.OPEN) { socket.send(JSON.stringify(payload)); return }
    try { const data = await request<{ reply: string; artifact?: DocumentArtifact; activities?: AgentActivity[] }>('/assistant/chat', { method: 'POST', body: JSON.stringify(payload) }); setMessages((items) => [...items, { role: 'agent', text: data.reply, artifact: data.artifact, activities: data.activities }]); if (data.artifact) setViewer(data.artifact) } catch (error) { const detail = error instanceof Error ? error.message : ''; const lower = detail.toLowerCase(); const message = lower.includes('schema cache') || lower.includes('user_settings') ? 'Kloppy can’t read your saved settings yet. Apply backend/db/003_user_settings.sql in Supabase, then retry.' : lower.includes('authentication') ? 'Your session has expired. Sign in again to continue.' : lower.includes('not configured') ? 'I’m not connected to my AI service yet. Add OPENROUTER_API_KEY to backend/.env, then restart the API.' : 'I couldn’t reach the campaign service just now. Please try again in a moment.'; setMessages((items) => [...items, { role: 'agent', text: message }]) } finally { setBusy(false); setActivities([]) }
  }

  const downloadArtifact = (artifact: DocumentArtifact) => {
    const url = URL.createObjectURL(new Blob([artifact.content], { type: 'text/markdown;charset=utf-8' }))
    const link = document.createElement('a')
    link.href = url
    link.download = artifact.filename || `${artifact.title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.md`
    link.click()
    URL.revokeObjectURL(url)
  }

  const savePermissionPolicy = async (policy: PermissionPolicy) => {
    setPermissionSaveError('')
    try {
      const current = await request<UserSettings>('/settings')
      const updated = await request<UserSettings>('/settings', {
        method: 'PUT',
        body: JSON.stringify({ ...current, permission_policy: policy }),
      })
      setPermission(updated.permission_policy)
    } catch {
      setPermissionSaveError('Could not save this approval preference. The previous saved setting remains active.')
    }
  }

  const addFile = (event: ChangeEvent<HTMLInputElement>) => { const names = Array.from(event.target.files ?? []).map((file) => file.name); setFiles((items) => [...items, ...names]); event.target.value = '' }
  const addContext = (label: string) => { setContextItems((items) => items.includes(label) ? items.filter((item) => item !== label) : [...items, label]); setMenuOpen(false) }
  const userHasSpoken = messages.some((message) => message.role === 'user')
  const startSpinOff = () => { const firstPrompt = messages.find((message) => message.role === 'user')?.text ?? ''; setSpinOffName(firstPrompt.trim().slice(0, 60)); setSpinOffOpen(true) }
  return <aside className={`assistant-panel ${fullPage ? 'full-page-chat' : ''}`}>
    <div className="assistant-head"><div><h2>What should we make true?</h2><span className="assistant-runtime"><span className="live-dot" /> {socket ? 'Live via WebSocket' : 'Ready for a message'}</span></div><button className="more-button" aria-label="Assistant options"><Icon name="dots" /></button></div>
    {messages.length === 0 && fullPage && <section className="chat-empty-state" aria-labelledby="chat-empty-title"><span className="chat-empty-mark"><KloppyMark /></span><h1 id="chat-empty-title">{campaignId ? `What would you like to make true for ${campaignName}?` : 'What are you launching?'}</h1><p>{campaignId ? 'Share the outcome you want from this campaign. Kloppy will keep the conversation, research, and drafts in this campaign’s workspace.' : 'Tell Kloppy about the product, the people you want to reach, or the result you want to create. We’ll shape the next move together.'}</p><div className="chat-starters" aria-label="Suggested starting points">{(campaignId ? ['Shape the campaign brief', 'Find the right audience', 'Draft launch messaging'] : ['We’re launching a new product', 'Help me find the right audience', 'Shape a campaign from my brief']).map((prompt) => <button type="button" key={prompt} onClick={() => { setInput(prompt); inputRef.current?.focus() }}>{prompt}<Icon name="arrow" size={14} /></button>)}</div></section>}
    <div className="chat-thread">{messages.map((message, index) => <div className={`chat-message ${message.role}`} key={`${message.text}-${index}`}><span className="chat-avatar">{message.role === 'agent' ? <KloppyMark /> : 'AK'}</span><div>{message.role === 'agent' ? <FormattedText text={message.text} /> : <p>{message.text}</p>}{message.activities && <ActivityFeed events={message.activities} />}{message.artifact && <button className="artifact-link" onClick={() => setViewer(message.artifact)}><Icon name="file" size={14} /> View {message.artifact.title}</button>}</div></div>)}{busy && <div className="chat-message agent"><span className="chat-avatar"><KloppyMark /></span><div><ActivityFeed events={activities} live /><p className="working-copy">Kloppy is preparing your response.</p></div></div>}</div>
    {!campaignId && userHasSpoken && <div className="conversation-actions"><button type="button" className="text-button" onClick={startSpinOff}><Icon name="plus" size={14} /> Spin off as a campaign</button>{spinOffOpen && <form onSubmit={(event) => { event.preventDefault(); if (spinOffName.trim()) onSpinOffCampaign?.(spinOffName.trim(), messages) }}><input aria-label="New campaign name" autoFocus value={spinOffName} onChange={(event) => setSpinOffName(event.target.value)} placeholder="Name this campaign" maxLength={200} required /><button className="button primary" type="submit"><Icon name="arrow" size={14} /> Create campaign</button><button type="button" className="text-button" onClick={() => setSpinOffOpen(false)}>Cancel</button></form>}</div>}
    {(files.length > 0 || contextItems.length > 0) && <div className="composer-context">{[...files, ...contextItems].map((item) => <span key={item}><Icon name={files.includes(item) ? 'file' : 'book'} size={12} /> {item}<button onClick={() => files.includes(item) ? setFiles((items) => items.filter((entry) => entry !== item)) : setContextItems((items) => items.filter((entry) => entry !== item))} aria-label={`Remove ${item}`}>×</button></span>)}</div>}
    {menuOpen && <div className="composer-menu"><label className="menu-action"><Icon name="file" size={15} /> Add files<input type="file" multiple onChange={addFile} /></label><button className={contextItems.includes('Brand knowledge') ? 'selected' : ''} onClick={() => addContext('Brand knowledge')}><Icon name="book" size={15} /> Brand knowledge</button><button className={contextItems.includes('Campaign skills') ? 'selected' : ''} onClick={() => addContext('Campaign skills')}><Icon name="spark" size={15} /> Campaign skills</button></div>}
    <form className="chat-composer" onSubmit={(e) => { e.preventDefault(); void send() }}><div className="composer-main"><button type="button" className={`composer-plus ${menuOpen ? 'active' : ''}`} aria-label="Add files, knowledge, or skills" onClick={() => setMenuOpen(!menuOpen)}><Icon name="plus" size={18} /></button><textarea ref={inputRef} aria-label="Ask Kloppy" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); void send() } }} placeholder="Ask Kloppy…" rows={1} /><button type="submit" className="composer-send" aria-label="Send message" disabled={!input.trim() || busy}><Icon name="send" size={17} /></button></div><div className="composer-controls"><label className="composer-select"><Icon name="lock" size={13} /><select aria-label="Permission policy" value={permission} onChange={(e) => void savePermissionPolicy(e.target.value as PermissionPolicy)}><option value="ask">Ask before actions</option><option value="auto">Auto-run drafts</option></select></label></div></form>
    <span className="assistant-note">{permissionSaveError || (permission === 'ask' ? 'Kloppy checks your saved settings and asks before consequential actions.' : 'Drafts may run automatically; publishing and spend still require your explicit approval.')}</span>
    {viewer && <div className="artifact-viewer" role="dialog" aria-modal="true" aria-labelledby="artifact-title"><div className="artifact-head"><div><span className="eyebrow">Markdown draft · ready to review</span><h3 id="artifact-title">{viewer.title}</h3></div><div className="artifact-actions"><button className="button secondary" onClick={() => downloadArtifact(viewer)}><Icon name="file" size={14} /> Download .md</button><button className="more-button" aria-label="Close document" onClick={() => setViewer(undefined)}>×</button></div></div><div className="document-preview"><FormattedText text={viewer.content} /></div></div>}
  </aside>
}

function ChatPage({ campaignId, campaignName, onSpinOffCampaign }: { campaignId?: string; campaignName?: string; onSpinOffCampaign: (name: string, messages: ChatMessage[]) => void }) {
  return <section className="chat-page"><Assistant fullPage campaignId={campaignId} campaignName={campaignName} onSpinOffCampaign={onSpinOffCampaign} /></section>
}

function Overview({ campaignName, onNavigate }: { campaignName: string; onNavigate: (prompt: string) => void }) {
  const steps = [
    { title: 'Brief', detail: 'Add product and launch context', icon: 'brief' as IconName },
    { title: 'Audience', detail: 'Explore evidence and hypotheses', icon: 'insights' as IconName },
    { title: 'Strategy', detail: 'Choose a clear direction', icon: 'strategy' as IconName },
    { title: 'Creative', detail: 'Draft campaign assets', icon: 'creative' as IconName },
    { title: 'Launch', detail: 'Review before action', icon: 'play' as IconName },
  ]
  const startBrief = 'Help me shape the brief for this campaign.'
  return <>
    <section className="page-heading campaign-overview-heading"><div><div className="heading-meta">Campaign workspace · Brief not started</div><h1>{campaignName}</h1><p className="heading-copy">This campaign has its own conversation and work. Start with the brief; Kloppy will keep decisions and drafts under this campaign.</p></div><button className="button primary" onClick={() => onNavigate(startBrief)}><KloppyMark /> Open Kloppy</button></section>
    <section className="journey-panel"><div className="journey-header"><div><span className="section-kicker">Campaign journey</span><h2>One campaign, from brief to learning</h2></div><span className="journey-status">Ready for your brief</span></div><div className="journey-track">{steps.map((step, index) => <div className={`journey-step ${index === 0 ? 'current' : 'next'}`} key={step.title}><div className="journey-node"><Icon name={step.icon} size={17} /></div><span>{step.title}</span><small>{step.detail}</small></div>)}</div></section>
    <div className="campaign-overview-grid"><article className="panel overview-empty-card"><span className="section-kicker">Start here</span><h2>Give Kloppy the campaign brief.</h2><p>Share the product, the people you want to reach, and what a successful launch would make true. Start with only what you know.</p><button className="text-button" onClick={() => onNavigate(startBrief)}><KloppyMark /> Add campaign context <Icon name="arrow" size={14} /></button></article><aside className="overview-next-card"><Icon name="activity" size={19} /><span className="section-kicker">Next step</span><h2>No audience or strategy saved yet.</h2><p>Kloppy will show campaign-specific work here after you create it in this campaign’s chat.</p><button className="button secondary" onClick={() => onNavigate(startBrief)}>Continue in Kloppy <Icon name="arrow" size={14} /></button></aside></div>
  </>
}

function CampaignList({ campaigns, onCreate, onOpen }: { campaigns: Campaign[]; onCreate: (name: string) => void; onOpen: (campaign: Campaign) => void }) {
  const [name, setName] = useState('')
  const [createOpen, setCreateOpen] = useState(false)
  const createInput = useRef<HTMLInputElement>(null)
  useEffect(() => { if (createOpen) createInput.current?.focus() }, [createOpen])
  return <><div className="page-heading compact campaigns-heading"><div><div className="heading-meta">Campaign workspaces</div><h1>Every campaign has its own room.</h1><p className="heading-copy">Each campaign keeps a separate name, conversation, and working context.</p></div><div className="campaign-create-anchor"><button className="button primary campaign-create-trigger" type="button" aria-expanded={createOpen} aria-controls="campaign-create-popover" onClick={() => setCreateOpen((open) => !open)}><Icon name="plus" size={16} /><span>Create new campaign</span></button>{createOpen && <form id="campaign-create-popover" className="campaign-create-popover" onSubmit={(event) => { event.preventDefault(); if (name.trim()) { onCreate(name.trim()); setName(''); setCreateOpen(false) } }}><h2>Give this campaign a name.</h2><label htmlFor="campaign-name">Campaign name</label><input ref={createInput} id="campaign-name" value={name} onChange={(event) => setName(event.target.value)} placeholder="For example, Spring product launch" maxLength={200} required /><div className="campaign-create-actions"><button className="button secondary" type="button" onClick={() => { setCreateOpen(false); setName('') }}>Cancel</button><button className="button primary" type="submit" disabled={!name.trim()}><Icon name="plus" size={15} /> Create campaign</button></div></form>}</div></div><section className="campaign-list" aria-label="Your campaigns">{campaigns.length ? campaigns.map((campaign) => <button className="campaign-list-item panel" key={campaign.id} onClick={() => onOpen(campaign)}><span className="integration-icon"><Icon name="campaigns" size={20} /></span><span><small>Campaign workspace</small><strong>{campaign.name}</strong><small>Created {new Date(campaign.createdAt).toLocaleDateString()}</small></span><Icon name="arrow" size={16} /></button>) : <div className="panel campaign-empty"><span className="section-kicker">No campaigns yet</span><h2>Name the first one to get started.</h2><p>Your campaign chat and decisions will be saved under its name.</p></div>}</section></>
}

function StagePage({ page, onAsk, onCampaignOpen, searchQuery = '' }: { page: 'campaigns' | 'audience' | 'strategy' | 'launch'; onAsk: (prompt: string) => void; onCampaignOpen?: () => void; searchQuery?: string }) {
  const content = {
    campaigns: { eyebrow: 'Campaign history', title: 'Every launch, still useful.', copy: 'Open a named campaign to keep its conversation, decisions, and drafts together.', action: 'Start a campaign', icon: 'campaigns' as IconName, items: ['Create a named campaign', 'Open a campaign workspace'] },
    audience: { eyebrow: 'Audience intelligence', title: 'Know who to make it for.', copy: 'Build audience hypotheses from the product brief and available evidence. Qloo signals are directional, never proof of purchase intent.', action: 'Ask Kloppy for an audience read', icon: 'insights' as IconName, items: ['Share the product and market', 'Explore cultural affinity signals', 'Compare audience hypotheses'] },
    strategy: { eyebrow: 'Strategy', title: 'Make the next decision clearer.', copy: 'Connect positioning, messages, channels, and success measures to this campaign’s brief and audience evidence.', action: 'Ask Kloppy to develop strategy', icon: 'strategy' as IconName, items: ['Draft positioning and promise', 'Build message pillars', 'Choose channels and success measures'] },
    launch: { eyebrow: 'Launch & learn', title: 'Move from ready to live.', copy: 'Review what is approved, check which tools are connected, and prepare the measurement plan before launch.', action: 'Ask Kloppy to prepare a launch review', icon: 'trend' as IconName, items: ['Review campaign approvals', 'Check connected publishing tools', 'Prepare a measurement plan'] },
  }[page]
  const filteredItems = content.items.filter((item) => !searchQuery.trim() || item.toLowerCase().includes(searchQuery.toLowerCase()))
  return <><div className="page-heading compact"><div><div className="heading-meta">{content.eyebrow}</div><h1>{content.title}</h1><p className="heading-copy">{content.copy}</p></div><button className="button primary" onClick={() => onAsk(content.action)}><KloppyMark /> Kloppy</button></div><section className="stage-layout"><div className="stage-main panel"><div className="stage-title"><div className="integration-icon"><Icon name={content.icon} size={21} /></div><div><span className="section-kicker">Campaign work</span><h2>{content.action}</h2></div></div><p className="stage-description">This view stays scoped to the selected campaign. Ask Kloppy to create the work, then review what has actually been saved here.</p><div className="stage-items">{filteredItems.length ? filteredItems.map((item, index) => <button key={item} onClick={() => page === 'campaigns' ? onCampaignOpen?.() : onAsk(`${content.action}: ${item}`)}><span>{String(index + 1).padStart(2, '0')}</span><strong>{item}</strong><Icon name="arrow" size={15} /></button>) : <div className="stage-empty">No actions match “{searchQuery}”. Try another search.</div>}</div></div><aside className="stage-aside"><span className="section-kicker">Campaign context</span><h2>Work stays with this campaign.</h2><p>Kloppy keeps the conversation for this campaign separate from your other campaign workspaces.</p><button className="text-button" onClick={() => onAsk(content.action)}><KloppyMark /> Open Kloppy <Icon name="arrow" size={14} /></button></aside></section></>
}

function Knowledge({ onNavigate }: { onNavigate: (page: Page) => void }) {
  const [sources, setSources] = useState<KnowledgeSource[]>([])
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [addMenuOpen, setAddMenuOpen] = useState(false)
  const [textOpen, setTextOpen] = useState(false)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const documentRef = useRef<HTMLInputElement>(null)
  const refresh = () => request<KnowledgeSource[]>('/knowledge/sources').then(setSources)
  useEffect(() => { refresh().catch((reason) => setError(reason instanceof Error ? reason.message : 'Could not load brand sources.')).finally(() => setLoading(false)) }, [])
  const saveText = async (event: FormEvent) => {
    event.preventDefault(); setBusy(true); setError('')
    try {
      const saved = await request<KnowledgeSource>('/knowledge/sources', { method: 'POST', body: JSON.stringify({ title, content, source_type: 'brand_text' }) })
      setSources((items) => [saved, ...items]); setTitle(''); setContent(''); setTextOpen(false); setAddMenuOpen(false)
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not save this source.') } finally { setBusy(false) }
  }
  const uploadDocument = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]; event.target.value = ''
    if (!file) return
    setBusy(true); setError('')
    const data = new FormData(); data.append('file', file)
    try {
      const saved = await uploadRequest<KnowledgeSource>('/knowledge/sources/document', data)
      setSources((items) => [saved, ...items]); setAddMenuOpen(false)
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not upload this document.') } finally { setBusy(false) }
  }
  const removeSource = async (id: string) => {
    setError('')
    try { await request<void>(`/knowledge/sources/${encodeURIComponent(id)}`, { method: 'DELETE' }); setSources((items) => items.filter((item) => item.id !== id)) }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not remove this source.') }
  }
  return <>
    <div className="page-heading compact"><div><div className="heading-meta">Workspace knowledge</div><h1>Give Kloppy the right context.</h1><p className="heading-copy">Save the facts, voice, and product details Kloppy should use across your campaigns.</p></div><div className="knowledge-actions"><button className="button secondary" onClick={() => onNavigate('integrations')}><Icon name="plug" size={16} /> Connect a source</button><button className="button primary" onClick={() => setAddMenuOpen(!addMenuOpen)}><Icon name="plus" size={16} /> Add a source</button></div></div>
    {addMenuOpen && <div className="knowledge-add-menu"><button onClick={() => documentRef.current?.click()} disabled={busy}><Icon name="file" size={15} /> Add a document <small>PDF, DOCX, TXT, or Markdown · 8 MB max</small></button><button onClick={() => { setTextOpen(true); setAddMenuOpen(false) }}><Icon name="book" size={15} /> Add brand text <small>Save positioning, voice, product facts, and guidelines</small></button><input ref={documentRef} type="file" accept=".pdf,.docx,.txt,.md,text/plain,text/markdown,application/pdf" onChange={uploadDocument} hidden /></div>}
    {textOpen && <form className="brand-source-form panel" onSubmit={saveText}><div><h2>Add brand context</h2><p>Kloppy will use this as user-provided context in future conversations.</p></div><label>Source title<input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Brand voice or product facts" maxLength={200} required /></label><label>Brand information<textarea value={content} onChange={(event) => setContent(event.target.value)} placeholder="Describe your brand, product, audience, claims to avoid, or preferred voice…" maxLength={100000} rows={7} required /></label><div className="brand-source-actions"><button type="button" className="button secondary" onClick={() => setTextOpen(false)}>Cancel</button><button type="submit" className="button primary" disabled={busy || !title.trim() || !content.trim()}>{busy ? 'Saving…' : 'Save source'} <Icon name="arrow" size={14} /></button></div></form>}
    {error && <div className="knowledge-error" role="alert">{error}</div>}
    <div className="knowledge-layout"><section className="knowledge-sources"><div className="knowledge-list-heading"><h2>Saved sources</h2><span>{sources.length} {sources.length === 1 ? 'source' : 'sources'}</span></div>{loading ? <div className="knowledge-empty panel">Loading saved sources…</div> : sources.length ? sources.map((source) => <article className="knowledge-source panel" key={source.id}><div className="knowledge-source-head"><div><span className="section-kicker">{source.source_type === 'document' ? 'Document' : 'Brand notes'}</span><h3>{source.title}</h3>{source.file_name && <small>{source.file_name}</small>}</div><button className="text-button" type="button" onClick={() => void removeSource(source.id)} aria-label={`Remove ${source.title}`}>Remove</button></div><details><summary>View saved content</summary><p>{source.content}</p></details></article>) : <section className="knowledge-empty panel"><div className="knowledge-empty-mark"><Icon name="book" size={23} /></div><h2>No sources saved yet.</h2><p>Add a document or write down the brand context Kloppy should carry between conversations. Saved sources are private to your account.</p></section>}</section><aside className="knowledge-aside"><span className="section-kicker">How Kloppy uses this</span><h2>Context before confidence.</h2><p>Saved brand material informs Kloppy’s responses. It stays separate from verified external evidence and campaign results.</p><div className="knowledge-rule"><Icon name="check" size={15} /><span>Sources are private to your account</span></div><div className="knowledge-rule"><Icon name="check" size={15} /><span>Remove outdated details any time</span></div></aside></div>
  </>
}

function Integrations({ searchQuery = '' }: { searchQuery?: string }) {
  const [items, setItems] = useState<IntegrationItem[]>([])
  const [filter, setFilter] = useState<'All' | 'Applications' | 'Resources'>('All')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [target, setTarget] = useState<IntegrationItem | 'custom' | null>(null)
  const [name, setName] = useState('')
  const [serverUrl, setServerUrl] = useState('')
  const [accessToken, setAccessToken] = useState('')
  const [toolOptions, setToolOptions] = useState<string[]>([])
  const [selectedTools, setSelectedTools] = useState<string[]>([])
  const [saving, setSaving] = useState(false)
  const [discovering, setDiscovering] = useState(false)
  const refresh = () => request<IntegrationItem[]>('/integrations').then(setItems)
  useEffect(() => { refresh().catch((reason) => setError(reason instanceof Error ? reason.message : 'Could not load integrations.')).finally(() => setLoading(false)) }, [])
  const openConnection = (item: IntegrationItem | 'custom') => {
    setTarget(item); setError(''); setToolOptions([]); setSelectedTools([]); setAccessToken('')
    if (item === 'custom') { setName(''); setServerUrl('') }
    else { setName(item.name); setServerUrl(item.server_url ?? ''); setSelectedTools(item.allowed_tools ?? []) }
  }
  const discover = async () => {
    setDiscovering(true); setError('')
    try {
      const result = await request<{ read_only_tools: string[] }>('/integrations/discover', { method: 'POST', body: JSON.stringify({ server_url: serverUrl, access_token: accessToken || null }) })
      setToolOptions(result.read_only_tools); setSelectedTools((current) => current.filter((tool) => result.read_only_tools.includes(tool)))
      if (!result.read_only_tools.length) setError('This MCP server did not advertise any read-only tools.')
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not inspect this server.') } finally { setDiscovering(false) }
  }
  const saveConnection = async (event: FormEvent) => {
    event.preventDefault(); setSaving(true); setError('')
    try {
      const payload = { name: name || undefined, server_url: serverUrl, access_token: accessToken || null, allowed_tools: selectedTools }
      const isCustom = target === 'custom' || (target !== null && typeof target === 'object' && target.id.startsWith('custom-'))
      const path = isCustom ? '/integrations/custom' : `/integrations/${encodeURIComponent(target !== null && typeof target === 'object' ? target.id : '')}/connect`
      await request<IntegrationItem>(path, { method: 'POST', body: JSON.stringify(payload) })
      await refresh(); setTarget(null)
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not connect this service.') } finally { setSaving(false) }
  }
  const disconnect = async (item: IntegrationItem) => {
    setError('')
    try { await request<void>(`/integrations/${encodeURIComponent(item.id)}`, { method: 'DELETE' }); await refresh() }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not disconnect this service.') }
  }
  const visible = items.filter((item) => (filter === 'All' || item.kind === filter.slice(0, -1)) && (!searchQuery.trim() || `${item.name} ${item.category} ${item.description}`.toLowerCase().includes(searchQuery.toLowerCase())))
  return <><div className="page-heading compact"><div><h1>Connect the tools Kloppy uses.</h1><p className="heading-copy">Connect an MCP server to share its read-only tools with Kloppy. Each connection is verified and saved securely to your account.</p></div><button className="button primary" onClick={() => openConnection('custom')}><Icon name="plus" size={16} /> Add custom</button></div>
    {error && <div className="knowledge-error" role="alert">{error}</div>}
    {target && <form className="mcp-connect-form panel" onSubmit={saveConnection}><div className="mcp-connect-heading"><div><span className="section-kicker">{target === 'custom' ? 'Custom server' : target.connected ? 'Manage connection' : 'New connection'}</span><h2>{target === 'custom' ? 'Add a custom MCP server.' : `Connect ${target.name}.`}</h2></div><button type="button" className="text-button" onClick={() => setTarget(null)}>Close</button></div>{target === 'custom' && <label>Connection name<input value={name} onChange={(event) => setName(event.target.value)} placeholder="For example, Internal research" maxLength={100} required /></label>}<label>MCP server URL<input type="url" value={serverUrl} onChange={(event) => setServerUrl(event.target.value)} placeholder="https://provider.example/mcp" required /></label><label>Bearer token <span className="field-note">Optional. Encrypted before storage; leave blank for a public server.</span><input type="password" value={accessToken} onChange={(event) => setAccessToken(event.target.value)} autoComplete="new-password" placeholder="Paste a provider token" /></label><div className="mcp-discover-row"><button type="button" className="button secondary" onClick={() => void discover()} disabled={!serverUrl || discovering}>{discovering ? 'Checking server…' : 'Find read-only tools'}</button><span>Kloppy only enables tools marked read-only by the MCP server.</span></div>{toolOptions.length > 0 && <fieldset className="mcp-tool-options"><legend>Choose tools to enable</legend>{toolOptions.map((tool) => <label key={tool}><input type="checkbox" checked={selectedTools.includes(tool)} onChange={(event) => setSelectedTools((current) => event.target.checked ? [...current, tool] : current.filter((name) => name !== tool))} /> <code>{tool}</code></label>)}</fieldset>}{target !== 'custom' && target.allowed_tools?.length && toolOptions.length === 0 && <p className="field-note">Saved tools: {target.allowed_tools.join(', ')}. Find tools again to change them.</p>}<div className="brand-source-actions"><button type="button" className="button secondary" onClick={() => setTarget(null)}>Cancel</button><button type="submit" className="button primary" disabled={saving || !toolOptions.length || !selectedTools.length || (target === 'custom' && !name.trim())}>{saving ? 'Verifying…' : 'Connect'} <Icon name="arrow" size={14} /></button></div></form>}
    <div className="connector-toolbar"><div className="filter-tabs">{(['All', 'Applications', 'Resources'] as const).map((option) => <button className={filter === option ? 'active' : ''} key={option} onClick={() => setFilter(option)}>{option}<span>{option === 'All' ? items.length : items.filter((item) => item.kind === option.slice(0, -1)).length}</span></button>)}</div></div>
    {loading ? <div className="connector-empty">Loading connected services…</div> : <div className="connector-grid">{visible.length ? visible.map((item) => <article className="connector-card" key={item.id}><div className="connector-card-head"><div className={`connector-logo logo-${item.id}`}>{item.name.slice(0, 1).toUpperCase()}</div><span className={`connector-status ${item.connected ? 'connected' : ''}`}><span />{item.connected ? 'Connected' : 'Not connected'}</span></div><span className="integration-category">{item.kind} · {item.category}</span><h2>{item.name}</h2><p>{item.description}</p><div className="connector-card-foot"><span className="connector-scope">{item.connected ? `${item.allowed_tools?.length ?? 0} read-only tools enabled` : 'MCP endpoint required'}</span><div><button className="button secondary" onClick={() => openConnection(item)}>{item.connected ? 'Manage' : 'Connect'}</button>{item.connected && <button className="text-button disconnect-button" onClick={() => void disconnect(item)}>Disconnect</button>}</div></div></article>) : <div className="connector-empty">{searchQuery.trim() ? `No services match “${searchQuery}”.` : 'No tools are available.'}</div>}</div>}
  </>
}

function Settings() {
  const [profile, setProfile] = useState<UserSettings>({ name: '', workspace: '', digest_enabled: true, permission_policy: 'ask' })
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [retryCount, setRetryCount] = useState(0)
  useEffect(() => { setLoading(true); setError(''); request<UserSettings>('/settings').then(setProfile).catch(() => setError('Settings could not be loaded. Check the API connection and Supabase user_settings setup, then try again.')).finally(() => setLoading(false)) }, [retryCount])
  const save = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    try {
      const updated = await request<UserSettings>('/settings', { method: 'PUT', body: JSON.stringify(profile) })
      setProfile(updated)
      setSaved(true)
      setTimeout(() => setSaved(false), 2400)
    } catch (reason) {
      setSaved(false)
      setError(reason instanceof Error ? reason.message : 'Could not save settings.')
    }
  }
  return <><div className="page-heading compact"><div><div className="heading-meta">Account settings</div><h1>Set the room<br />up for better work.</h1><p className="heading-copy">Control how Kloppy speaks, where your work lives, and which decisions need your approval.</p></div></div><form className={`settings-layout ${error ? 'settings-unavailable' : ''}`} onSubmit={save}>{error && <div className="settings-load-error" role="alert"><Icon name="activity" size={16} /><div><strong>Saved settings are unavailable.</strong><span>Check the API connection and Supabase user_settings setup, then retry.</span></div><button type="button" className="button secondary" onClick={() => setRetryCount((count) => count + 1)}>Try again</button></div>}<section className="settings-section"><div><span className="section-kicker">Account identity</span><h2>How your team sees this space</h2><p>These details help Kloppy keep campaign language grounded in your world.</p></div><div className="settings-fields"><label>Your name<input required minLength={2} maxLength={80} value={profile.name} disabled={Boolean(error)} onChange={(event) => setProfile({ ...profile, name: event.target.value })} /></label><label>Organization name<input required minLength={2} maxLength={120} value={profile.workspace} disabled={Boolean(error)} onChange={(event) => setProfile({ ...profile, workspace: event.target.value })} /></label></div></section><section className="settings-section"><div><span className="section-kicker">Working style</span><h2>Keep the signal visible</h2><p>Drafting can happen quickly; publishing and spend always need clear approval.</p></div><div className="settings-fields"><label>Draft approval preference<select value={profile.permission_policy} disabled={Boolean(error)} onChange={(event) => setProfile({ ...profile, permission_policy: event.target.value as UserSettings['permission_policy'] })}><option value="ask">Ask before actions</option><option value="auto">Auto-run drafts</option></select></label><label className="toggle-row"><span><strong>Weekly campaign digest</strong><small>A short read on what changed and what deserves your attention.</small></span><input type="checkbox" checked={profile.digest_enabled} disabled={Boolean(error)} onChange={(event) => setProfile({ ...profile, digest_enabled: event.target.checked })} /><span className="toggle" /></label></div></section><div className="settings-footer"><span className={`secure-note ${error ? 'settings-error' : ''}`} role={error ? 'status' : undefined}><Icon name={error ? 'activity' : 'lock'} size={13} /> {loading ? 'Loading saved settings…' : error ? 'Settings unavailable' : 'Changes are saved privately.'}</span>{error ? null : <button className="button primary" type="submit" disabled={loading || Boolean(error)}>{saved ? 'Saved' : 'Save changes'} <Icon name={saved ? 'check' : 'arrow'} size={15} /></button>}</div></form></>
}
function CampaignTabs({ page, setPage }: { page: Page; setPage: (page: Page) => void }) {
  return <nav className="campaign-tabs" aria-label="Campaign sections">{campaignNav.map((item) => <button aria-label={item.label} className={page === item.page ? 'active' : ''} key={item.page} onClick={() => setPage(item.page)}>{item.page === 'campaign-chat' ? <KloppyMark /> : <Icon name={item.icon} size={15} />}<span>{item.page === 'launch' ? <><span className="tab-long-label">Launch &amp; learn</span><span className="tab-short-label">Launch</span></> : item.label}</span></button>)}</nav>
}

function App() {
  const initialRoute = window.location.hash.slice(1) || (localStorage.getItem('kloppy-session') ? 'chat' : 'landing')
  const [route, setRoute] = useState(initialRoute === 'creative' ? 'campaign-chat' : initialRoute); const [authMode, setAuthMode] = useState<AuthMode>('login'); const [user, setUser] = useState({ name: localStorage.getItem('kloppy-user-name') ?? 'My profile' }); const [searchQuery, setSearchQuery] = useState('')
  const [campaigns, setCampaigns] = useState<Campaign[]>(readCampaigns)
  const [selectedCampaignId, setSelectedCampaignId] = useState(() => localStorage.getItem(`kloppy-selected-campaign:${accountKey()}`) ?? '')
  const selectedCampaign = campaigns.find((item) => item.id === selectedCampaignId)
  const createCampaign = (name: string, conversation?: ChatMessage[]) => { const campaign = { id: crypto.randomUUID(), name, createdAt: new Date().toISOString() }; const next = [campaign, ...campaigns]; setCampaigns(next); localStorage.setItem(`kloppy-campaigns:${accountKey()}`, JSON.stringify(next)); if (conversation) localStorage.setItem(`kloppy-chat:${accountKey()}:${campaign.id}`, JSON.stringify(conversation)); setSelectedCampaignId(campaign.id); localStorage.setItem(`kloppy-selected-campaign:${accountKey()}`, campaign.id); go('campaign-chat') }
  const openCampaign = (campaign: Campaign) => { setSelectedCampaignId(campaign.id); localStorage.setItem(`kloppy-selected-campaign:${accountKey()}`, campaign.id); go('campaign-chat') }
  useEffect(() => {
    const sync = () => {
      const current = window.location.hash.slice(1) || 'landing'
      if (current === 'creative') {
        window.location.hash = 'campaign-chat'
        setRoute('campaign-chat')
        return
      }
      setRoute(current)
    }
    window.addEventListener('hashchange', sync)
    if (initialRoute === 'creative') window.location.hash = 'campaign-chat'
    return () => window.removeEventListener('hashchange', sync)
  }, [])
  const go = (next: string) => { window.location.hash = next }
  const askInCampaign = (prompt: string) => { if (selectedCampaign) sessionStorage.setItem(`kloppy-next-prompt:${accountKey()}:${selectedCampaign.id}`, prompt); go('campaign-chat') }
  const logout = () => { localStorage.removeItem('kloppy-session'); localStorage.removeItem('kloppy-user-name'); setCampaigns([]); setSelectedCampaignId(''); setAuthMode('login'); go('landing') }
  if (route === 'landing') return <Landing onAuth={(mode) => { setAuthMode(mode); go('auth') }} />
  if (route === 'auth') return <Auth mode={authMode} onMode={setAuthMode} onComplete={(nextUser) => { setUser(nextUser); localStorage.setItem('kloppy-user-name', nextUser.name); setCampaigns(readCampaigns()); setSelectedCampaignId(''); go('chat') }} />
  const pages: Page[] = ['chat', 'campaigns', 'knowledge', 'integrations', 'settings', 'campaign-chat', 'overview', 'audience', 'strategy', 'launch']
  const page = (pages.includes(route as Page) ? route : 'chat') as Page
  const pageTitle = page === 'chat' ? 'Kloppy' : page === 'knowledge' ? 'Knowledge' : ['campaign-chat', 'overview', 'audience', 'strategy', 'launch'].includes(page) ? campaignNav.find((item) => item.page === page)?.label ?? 'Campaign' : navItems.find((item) => item.page === page)?.label ?? page
  const hasStudio = ['campaign-chat', 'overview', 'audience', 'strategy', 'launch'].includes(page) && Boolean(selectedCampaign)
  const canSearch = page === 'campaigns' || page === 'integrations'
  return <div className="app-shell"><Sidebar page={page} setPage={(next) => go(next)} user={user} onLogout={logout} /><main className="main-content"><div className="workspace-header"><header className="topbar"><div className="breadcrumb"><span>Kloppy</span><Icon name="chevron" size={14} /><strong>{pageTitle}</strong></div>{hasStudio && selectedCampaign && <button className="campaign-name-chip" onClick={() => go('campaigns')} title="Switch campaign">{selectedCampaign.name}<Icon name="chevron" size={13} /></button>}{canSearch && <div className="topbar-actions"><label className="search-control"><Icon name="search" size={17} /><input aria-label={`Search ${page}`} value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} placeholder={page === 'campaigns' ? 'Search campaigns' : 'Search connectors'} /><kbd>⌘ K</kbd></label></div>}</header>{hasStudio && <CampaignTabs page={page} setPage={(next) => go(next)} />}</div><div className={page === 'chat' || page === 'campaign-chat' ? 'chat-page-wrap' : 'page-wrap'}>{page === 'chat' ? <ChatPage onSpinOffCampaign={createCampaign} /> : page === 'campaign-chat' ? selectedCampaign ? <ChatPage key={selectedCampaign.id} campaignId={selectedCampaign.id} campaignName={selectedCampaign.name} onSpinOffCampaign={createCampaign} /> : <CampaignList campaigns={campaigns} onCreate={createCampaign} onOpen={openCampaign} /> : null}{page === 'campaigns' && <CampaignList campaigns={campaigns} onCreate={createCampaign} onOpen={openCampaign} />}{page === 'knowledge' && <Knowledge onNavigate={(next) => go(next)} />}{page === 'overview' && (selectedCampaign ? <Overview campaignName={selectedCampaign.name} onNavigate={askInCampaign} /> : <CampaignList campaigns={campaigns} onCreate={createCampaign} onOpen={openCampaign} />)}{['audience', 'strategy', 'launch'].includes(page) && (selectedCampaign ? <StagePage page={page as 'audience' | 'strategy' | 'launch'} onAsk={askInCampaign} /> : <CampaignList campaigns={campaigns} onCreate={createCampaign} onOpen={openCampaign} />)}{page === 'integrations' && <Integrations searchQuery={searchQuery} />}{page === 'settings' && <Settings />}</div></main></div>
}

export default App
