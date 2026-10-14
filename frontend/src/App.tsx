import { type ChangeEvent, type FormEvent, type MouseEvent, type ReactNode, useEffect, useRef, useState } from 'react'
import './App.css'

type Page = 'chat' | 'campaigns' | 'knowledge' | 'integrations' | 'settings' | 'campaign-chat' | 'overview' | 'audience' | 'strategy' | 'launch'
type AuthMode = 'login' | 'signup'
type UserSettings = { name: string; workspace: string; digest_enabled: boolean; permission_policy: 'ask' | 'auto' }
type IconName = 'activity' | 'arrow' | 'brief' | 'campaigns' | 'chevron' | 'creative' | 'dots' | 'insights' | 'plus' | 'search' | 'settings' | 'spark' | 'strategy' | 'trend' | 'send' | 'lock' | 'check' | 'play' | 'book' | 'collapse' | 'external' | 'plug' | 'file' | 'eye' | 'eyeOff' | 'logout'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api'

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

const fallbackDashboard = {
  campaign: {
    name: 'Lagos product launch',
    status: 'In progress',
    updated: '12 min ago',
    headline: 'Good marketing starts with a better read.',
    description: 'Turn cultural signals into a campaign your audience can feel — and your team can ship.',
    insight: { title: 'Style is a social language.', description: 'The signal shows a strong affinity between Lagos design culture, independent music, and tools that make work feel personal.', confidence: 'Directional confidence' },
    strategy: { title: 'Make work feel like yours.', positioning: 'Marketing clarity for people building their own way.', pillar: 'Your next best move, not another dashboard.', channel: 'Instagram · Creator partnerships' },
  },
  segments: [
    { name: 'Culture-led early adopters', note: 'High affinity', signal: 'Cultural signal', color: 'coral' },
    { name: 'Practical momentum buyers', note: 'Good fit', signal: 'Product evidence', color: 'mint' },
    { name: 'Curious category switchers', note: 'Needs testing', signal: 'Market hypothesis', color: 'gold' },
  ],
}

const fallbackIntegrations = [
  { id: 'meta-ads', name: 'Meta Ads', kind: 'Application', category: 'Paid social', description: 'Draft audiences, ads, and spend plans for Instagram and Facebook.', status: 'Available', connected: false, logo: 'M' },
  { id: 'google-ads', name: 'Google Ads', kind: 'Application', category: 'Paid search', description: 'Prepare search and YouTube campaigns for review before launch.', status: 'Available', connected: false, logo: 'G' },
  { id: 'hubspot', name: 'HubSpot', kind: 'Application', category: 'CRM', description: 'Use contact lists and lifecycle context to shape campaign audiences.', status: 'Available', connected: false, logo: 'H' },
  { id: 'mailchimp', name: 'Mailchimp', kind: 'Application', category: 'Email', description: 'Create campaign drafts and send approved email journeys.', status: 'Available', connected: false, logo: 'M' },
  { id: 'canva', name: 'Canva', kind: 'Application', category: 'Design', description: 'Hand off approved briefs and retrieve ready-to-publish brand assets.', status: 'Available', connected: false, logo: 'C' },
  { id: 'figma', name: 'Figma', kind: 'Resource', category: 'Design files', description: 'Read campaign boards, brand systems, and feedback in one place.', status: 'Connected', connected: true, logo: 'F' },
  { id: 'google-drive', name: 'Google Drive', kind: 'Resource', category: 'Knowledge', description: 'Ground answers in briefs, research, catalogs, and past campaign files.', status: 'Connected', connected: true, logo: 'D' },
  { id: 'notion', name: 'Notion', kind: 'Resource', category: 'Knowledge', description: 'Bring launch notes, brand voice, and operating knowledge into context.', status: 'Available', connected: false, logo: 'N' },
  { id: 'ga4', name: 'Google Analytics', kind: 'Resource', category: 'Performance', description: 'Return traffic, conversion, and content signals to the campaign loop.', status: 'Available', connected: false, logo: 'A' },
  { id: 'shopify', name: 'Shopify', kind: 'Application', category: 'Commerce', description: 'Connect product, catalog, and storefront context for fashion launches.', status: 'Available', connected: false, logo: 'S' },
]

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
  }
  return <svg {...common}>{paths[name]}</svg>
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem('kloppy-session')
  const headers = new Headers(options?.headers)
  headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(`${API_URL}${path}`, { ...options, headers })
  if (!response.ok) throw new Error((await response.json()).detail ?? 'Request failed')
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
  return <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}><div className="sidebar-top"><Brand /><button className="sidebar-toggle" aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'} onClick={() => setCollapsed(!collapsed)}><Icon name="collapse" size={17} /></button></div><nav className="main-nav" aria-label="Main navigation">{navItems.filter((item) => item.page !== 'settings').map((item) => <button title={collapsed ? item.label : undefined} aria-label={item.label} className={`nav-item ${page === item.page ? 'active' : ''}`} key={item.page} onClick={() => setPage(item.page)}>{item.page === 'chat' ? <KloppyMark /> : <Icon name={item.icon} />}<span>{item.label}</span></button>)}</nav><div className="sidebar-bottom"><button className={`nav-item settings-nav ${page === 'settings' ? 'active' : ''}`} onClick={() => setPage('settings')}><Icon name="settings" /><span>Settings</span></button><div className="user-profile"><div className="user-avatar">{user.name.slice(0, 2).toUpperCase()}</div><div><strong>{user.name}</strong><span>Account owner</span></div><button className="logout-button" type="button" title="Log out" aria-label="Log out" onClick={onLogout}><Icon name="logout" size={16} /><span>Log out</span></button></div></div></aside>
}

type ChatMode = 'research' | 'plan' | 'execute'
type PermissionPolicy = 'ask' | 'auto'
type ChatMessage = { role: 'agent' | 'user'; text: string; artifact?: { title: string; content: string } }

const models = [
  { id: 'kloppy-balanced', label: 'Kloppy balanced', provider: 'Kloppy' },
  { id: 'claude-sonnet', label: 'Claude Sonnet', provider: 'Anthropic' },
  { id: 'gpt-5', label: 'GPT-5', provider: 'OpenAI' },
  { id: 'gemini-pro', label: 'Gemini Pro', provider: 'Google' },
]

const modeCopy: Record<ChatMode, { label: string; description: string }> = {
  research: { label: 'Research', description: 'Search and bring back grounded findings.' },
  plan: { label: 'Plan', description: 'Research first, then create a step-by-step document.' },
  execute: { label: 'Execute', description: 'Research, plan, and carry out approved work.' },
}

function Assistant({ fullPage = false, campaign = false, onConversationStart }: { fullPage?: boolean; campaign?: boolean; onConversationStart?: () => void }) {
  const [messages, setMessages] = useState<ChatMessage[]>([{ role: 'agent', text: 'I’m ready. Tell me what you’re trying to make true, and I’ll help shape the next move.' }])
  const [input, setInput] = useState(''); const [busy, setBusy] = useState(false); const [mode, setMode] = useState<ChatMode>('plan'); const [model, setModel] = useState(models[0].id); const [permission, setPermission] = useState<PermissionPolicy>('ask')
  const [permissionSaveError, setPermissionSaveError] = useState('')
  const [menuOpen, setMenuOpen] = useState(false); const [files, setFiles] = useState<string[]>([]); const [contextItems, setContextItems] = useState<string[]>([]); const [viewer, setViewer] = useState<ChatMessage['artifact']>(undefined); const [socket, setSocket] = useState<WebSocket | null>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    request<UserSettings>('/settings').then((saved) => setPermission(saved.permission_policy)).catch(() => setPermission('ask'))
  }, [])

  useEffect(() => {
    if (campaign) setMode('execute')
  }, [campaign])

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
      const data = JSON.parse(event.data) as { reply?: string; error?: string; artifact?: { title: string; content: string } }
      const errorMessage = data.error?.toLowerCase().includes('not configured')
        ? 'I’m not connected to my AI service yet. Add OPENROUTER_API_KEY to backend/.env, then restart the API.'
        : data.error ? 'I couldn’t complete that just now. Please try again in a moment.' : undefined
      setMessages((items) => [...items, { role: 'agent', text: data.reply ?? errorMessage ?? 'The agent returned no response.', artifact: data.artifact }])
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
    const payload = { message: value, mode, model, permission, attachments: files, context_items: contextItems, conversation_history }
    onConversationStart?.()
    setMessages((items) => [...items, { role: 'user', text: value }]); setInput(''); setBusy(true)
    if (socket?.readyState === WebSocket.OPEN) { socket.send(JSON.stringify(payload)); return }
    try { const data = await request<{ reply: string; artifact?: { title: string; content: string } }>('/assistant/chat', { method: 'POST', body: JSON.stringify(payload) }); setMessages((items) => [...items, { role: 'agent', text: data.reply, artifact: data.artifact }]) } catch (error) { const detail = error instanceof Error ? error.message : ''; const message = detail.toLowerCase().includes('not configured') ? 'I’m not connected to my AI service yet. Add OPENROUTER_API_KEY to backend/.env, then restart the API.' : 'I couldn’t reach the campaign service just now. Please try again in a moment.'; setMessages((items) => [...items, { role: 'agent', text: message }]) } finally { setBusy(false) }
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
  return <aside className={`assistant-panel ${fullPage ? 'full-page-chat' : ''}`}>
    <div className="assistant-head"><div><h2>What should we make true?</h2><span className="assistant-runtime"><span className="live-dot" /> {socket ? 'Live via WebSocket' : 'Ready for a message'}</span></div><button className="more-button" aria-label="Assistant options"><Icon name="dots" /></button></div>
    <div className="chat-thread">{messages.map((message, index) => <div className={`chat-message ${message.role}`} key={`${message.text}-${index}`}><span className="chat-avatar">{message.role === 'agent' ? <KloppyMark /> : 'AK'}</span><div>{message.role === 'agent' ? <FormattedText text={message.text} /> : <p>{message.text}</p>}{message.artifact && <button className="artifact-link" onClick={() => setViewer(message.artifact)}><Icon name="file" size={14} /> View {message.artifact.title}</button>}</div></div>)}{busy && <div className="chat-message agent"><span className="chat-avatar"><KloppyMark /></span><p className="thinking"><i /><i /><i /></p></div>}</div>
    {!messages.some((message) => message.role === 'user') && <div className="prompt-chips">{(campaign ? ['Create campaign assets', 'Write social post variations', 'Develop a visual direction'] : ['What should I do next?', 'Find my first audience', 'Build the campaign plan']).map((suggestion) => <button key={suggestion} onClick={() => send(suggestion)}>{suggestion}</button>)}</div>}
    {(files.length > 0 || contextItems.length > 0) && <div className="composer-context">{[...files, ...contextItems].map((item) => <span key={item}><Icon name={files.includes(item) ? 'file' : 'book'} size={12} /> {item}<button onClick={() => files.includes(item) ? setFiles((items) => items.filter((entry) => entry !== item)) : setContextItems((items) => items.filter((entry) => entry !== item))} aria-label={`Remove ${item}`}>×</button></span>)}</div>}
    {menuOpen && <div className="composer-menu"><label className="menu-action"><Icon name="file" size={15} /> Add files<input type="file" multiple onChange={addFile} /></label><button className={contextItems.includes('Brand knowledge') ? 'selected' : ''} onClick={() => addContext('Brand knowledge')}><Icon name="book" size={15} /> Brand knowledge</button><button className={contextItems.includes('Campaign skills') ? 'selected' : ''} onClick={() => addContext('Campaign skills')}><Icon name="spark" size={15} /> Campaign skills</button></div>}
    <form className="chat-composer" onSubmit={(e) => { e.preventDefault(); void send() }}><div className="composer-main"><button type="button" className={`composer-plus ${menuOpen ? 'active' : ''}`} aria-label="Add files, knowledge, or skills" onClick={() => setMenuOpen(!menuOpen)}><Icon name="plus" size={18} /></button><textarea ref={inputRef} aria-label="Ask Kloppy" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); void send() } }} placeholder={`Ask Kloppy to ${modeCopy[mode].label.toLowerCase()}…`} rows={1} /><button type="submit" className="composer-send" aria-label="Send message" disabled={!input.trim() || busy}><Icon name="send" size={17} /></button></div><div className="composer-controls"><label className="composer-select"><Icon name="spark" size={13} /><select aria-label="Chat mode" value={mode} onChange={(e) => setMode(e.target.value as ChatMode)}>{Object.entries(modeCopy).map(([value, copy]) => <option value={value} key={value}>{copy.label}</option>)}</select></label><label className="composer-select"><Icon name="activity" size={13} /><select aria-label="Model" value={model} onChange={(e) => setModel(e.target.value)}>{models.map((item) => <option value={item.id} key={item.id}>{item.label}</option>)}</select></label><label className="composer-select"><Icon name="lock" size={13} /><select aria-label="Permission policy" value={permission} onChange={(e) => void savePermissionPolicy(e.target.value as PermissionPolicy)}><option value="ask">Ask before actions</option><option value="auto">Auto-run drafts</option></select></label></div></form>
    <span className="assistant-note">{permissionSaveError || `${modeCopy[mode].description} ${permission === 'ask' ? 'Kloppy checks your saved settings and asks before consequential actions.' : 'Drafting may run automatically; publishing and spend still require your explicit approval.'}`}</span>
    {viewer && <div className="artifact-viewer" role="dialog" aria-modal="true"><div className="artifact-head"><div><span className="eyebrow">Generated document</span><h3>{viewer.title}</h3></div><button className="more-button" aria-label="Close document" onClick={() => setViewer(undefined)}>×</button></div><pre>{viewer.content}</pre></div>}
  </aside>
}

function ChatPage({ campaign = false }: { campaign?: boolean }) {
  const [conversationStarted, setConversationStarted] = useState(false)
  return <section className={`chat-page ${conversationStarted ? 'conversation-started' : ''}`}>{!conversationStarted && <div className="chat-page-intro"><h1>{campaign ? 'Make your campaign with Kloppy.' : 'What should we make true?'}</h1><p>{campaign ? 'Build strategy, copy, and creative in one conversation. Kloppy keeps the brief, decisions, and campaign work connected.' : 'Bring a brief, a question, or a half-formed idea. Kloppy will help you find the signal and shape the next campaign.'}</p></div>}<Assistant fullPage campaign={campaign} onConversationStart={() => setConversationStarted(true)} /></section>
}

function Overview({ data, onNavigate }: { data: typeof fallbackDashboard; onNavigate: (prompt: string) => void }) {
  const [selected, setSelected] = useState(0); const [approved, setApproved] = useState(false)
  return <><section className="page-heading"><div><div className="heading-meta"><span className="live-dot" /> Campaign in progress <span className="meta-divider" /> Last updated {data.campaign.updated}</div><h1>{data.campaign.headline}</h1><p className="heading-copy">{data.campaign.description}</p></div><button className="button primary" onClick={() => onNavigate('Build a campaign plan')}><Icon name="plus" size={16} /> New campaign</button></section><section className="journey-panel"><div className="journey-header"><div><span className="section-kicker">Campaign journey</span><h2>From signal to signal boost</h2></div><button className="text-button" onClick={() => onNavigate('Open the campaign map')} >Open campaign map <Icon name="arrow" size={15} /></button></div><div className="journey-track"><div className="journey-line" />{['Brief', 'Audience', 'Strategy', 'Creative', 'Launch'].map((step, index) => <div className={`journey-step ${index < 2 ? 'complete' : index === 2 ? 'current' : 'next'}`} key={step}><div className="journey-node"><Icon name={['brief', 'insights', 'strategy', 'creative', 'play'][index] as IconName} size={17} /></div><span>{step}</span>{index === 2 && <small>In review</small>}</div>)}</div></section><div className="dashboard-grid"><article className="panel"><div className="panel-head"><div><span className="section-kicker">Audience intelligence</span><h2>What the signal says</h2></div><Icon name="spark" size={18} /></div><div className="insight-callout"><div className="spark-icon"><Icon name="spark" size={19} /></div><div><strong>{data.campaign.insight.title}</strong><p>{data.campaign.insight.description}</p></div></div><div className="source-row"><span className="source-badge">EVIDENCE</span><span>{data.campaign.insight.confidence}</span><button className="inline-link" onClick={() => onNavigate('Show me the evidence')}>See evidence <Icon name="arrow" size={13} /></button></div></article><article className="panel"><div className="panel-head"><div><span className="section-kicker">Your next decision</span><h2>Choose a first audience</h2></div><span className="step-chip">02 / 04</span></div><p className="panel-intro">Pick the audience to shape your message around. You can change this before launch.</p><div className="segment-list">{data.segments.map((segment, index) => <button className={`segment-row ${selected === index ? 'selected' : ''}`} key={segment.name} onClick={() => setSelected(index)}><span className={`segment-marker ${segment.color}`} /><span className="segment-info"><strong>{segment.name}</strong><small>{segment.signal}</small></span><span className={`fit-label ${segment.color}`}>{segment.note}</span><span className="radio-indicator" /></button>)}</div></article></div><div className="bottom-grid"><article className="panel"><div className="panel-head"><div><span className="section-kicker">Strategy draft</span><h2>{data.campaign.strategy.title}</h2></div><span className="draft-status"><span /> Draft</span></div><div className="strategy-body"><div><span className="label">Positioning</span><p>{data.campaign.strategy.positioning}</p></div><div><span className="label">Message pillar</span><p className="quoted">“{data.campaign.strategy.pillar}”</p></div><div><span className="label">Recommended channel</span><p>{data.campaign.strategy.channel}</p></div></div><button className="text-button small" onClick={() => onNavigate('Review the strategy')}>Review strategy <Icon name="arrow" size={14} /></button></article><article className={`launch-panel ${approved ? 'approved' : ''}`}><div className="launch-orbit"><div className="orbit-ring ring-one" /><div className="orbit-ring ring-two" /><div className="launch-core"><Icon name={approved ? 'trend' : 'play'} size={25} /></div></div><span className="section-kicker">{approved ? 'Ready for creative' : 'One step at a time'}</span><h2>{approved ? 'Audience selected.' : 'Make the signal useful.'}</h2><p>{approved ? 'Your strategy can now move into creative production.' : `Select “${data.segments[selected].name}” to make it the lead audience.`}</p><button className="button launch-button" onClick={() => setApproved(!approved)}>{approved ? 'Undo selection' : 'Approve audience'} <Icon name={approved ? 'check' : 'arrow'} size={15} /></button></article></div></>
}

function StagePage({ page, onAsk, onCampaignOpen, searchQuery = '' }: { page: 'campaigns' | 'audience' | 'strategy' | 'launch'; onAsk: (prompt: string) => void; onCampaignOpen?: () => void; searchQuery?: string }) {
  const content = {
    campaigns: { eyebrow: 'Campaign history', title: 'Every launch, still useful.', copy: 'Keep the decisions, assets, and learnings from every campaign your business has carried out.', action: 'Start a campaign', icon: 'campaigns' as IconName, items: ['Oyin Fab Studio · Lagos capsule', 'Ame Studio · Harmattan edit', 'Oyin Fab Studio · Community pop-up', 'Ame Studio · Founder story'] },
    audience: { eyebrow: 'Audience intelligence', title: 'Know who to make it for.', copy: 'Turn a product brief into audience directions with evidence, confidence, and a clear next question.', action: 'Ask for an audience read', icon: 'insights' as IconName, items: ['Culture-led early adopters', 'Practical momentum buyers', 'Curious category switchers'] },
    strategy: { eyebrow: 'Strategy', title: 'Make the next decision clearer.', copy: 'Keep positioning, message pillars, channels, and trade-offs connected to the audience you chose.', action: 'Review the strategy', icon: 'strategy' as IconName, items: ['Positioning draft', 'Message architecture', 'Channel recommendation'] },
    launch: { eyebrow: 'Launch & learn', title: 'Move from ready to live.', copy: 'Review what is authorized, execute through connected business tools, and bring performance back into the next decision.', action: 'Prepare launch review', icon: 'trend' as IconName, items: ['Approval checklist', 'Execution queue', 'Performance readback'] },
  }[page]
  const filteredItems = content.items.filter((item) => !searchQuery.trim() || item.toLowerCase().includes(searchQuery.toLowerCase()))
  return <><div className="page-heading compact"><div><div className="heading-meta">{content.eyebrow}</div><h1>{content.title}</h1><p className="heading-copy">{content.copy}</p></div><button className="button primary" onClick={() => onAsk(content.action)}><KloppyMark /> Kloppy</button></div><section className="stage-layout"><div className="stage-main panel"><div className="stage-title"><div className="integration-icon"><Icon name={content.icon} size={21} /></div><div><span className="section-kicker">Campaign work</span><h2>{content.action}</h2></div></div><p className="stage-description">Kloppy can prepare this with the connected context in your account, then pause for your review before anything consequential happens.</p><div className="stage-items">{filteredItems.length ? filteredItems.map((item, index) => <button key={item} onClick={() => page === 'campaigns' ? onCampaignOpen?.() : onAsk(`${content.action}: ${item}`)}><span>{String(index + 1).padStart(2, '0')}</span><strong>{item}</strong><Icon name="arrow" size={15} /></button>) : <div className="stage-empty">No campaigns match “{searchQuery}”. Try a name, channel, or collection.</div>}</div></div><aside className="stage-aside"><span className="section-kicker">Campaign context</span><h2>Ready for your direction.</h2><p>Ask for a draft, a comparison, or the next action. You decide what becomes real.</p><button className="text-button" onClick={() => onAsk(content.action)}><KloppyMark /> Open Kloppy <Icon name="arrow" size={14} /></button></aside></section></>
}

function Knowledge() {
  const entries = [
    ['Brand voice', 'Oyin Fab Studio is precise, warm, and self-possessed. We speak about clothes as a way to enter a room with intention.'],
    ['Customer truth', 'Customers want pieces that work across Lagos days: a client meeting, a gallery opening, and the dinner after.'],
    ['Collection note', 'The Lagos capsule pairs breathable cottons with sculptural tailoring and colour drawn from late-afternoon street light.'],
    ['Proof to protect', 'Only use product details, prices, stock, and delivery promises that the team has confirmed.'],
  ]
  return <><div className="page-heading compact"><div><div className="heading-meta">Knowledge library</div><h1>Give Kloppy the right context.</h1><p className="heading-copy">A small, living library for the facts, voice, and decisions that should travel with every campaign.</p></div><button className="button primary"><Icon name="plus" size={16} /> Add knowledge</button></div><div className="knowledge-layout"><section className="knowledge-list">{entries.map(([title, text]) => <article className="knowledge-entry" key={title}><div className="knowledge-entry-top"><span className="section-kicker">Campaign note</span><button className="more-button" aria-label={`More options for ${title}`}><Icon name="dots" size={16} /></button></div><h2>{title}</h2><p>{text}</p><span className="knowledge-source"><Icon name="brief" size={13} /> Added by Amara · private</span></article>)}</section><aside className="knowledge-aside"><span className="section-kicker">How Kloppy uses this</span><h2>Context before confidence.</h2><p>Knowledge is available to the agent as background. It never overrides a current brief, approved strategy, or connected source.</p><div className="knowledge-rule"><Icon name="check" size={15} /><span>Facts stay attributable</span></div><div className="knowledge-rule"><Icon name="check" size={15} /><span>Outdated notes can be archived</span></div></aside></div></>
}

function Integrations({ searchQuery = '' }: { searchQuery?: string }) {
  const [items, setItems] = useState(fallbackIntegrations)
  const [filter, setFilter] = useState<'All' | 'Applications' | 'Resources'>('All')
  const [customOpen, setCustomOpen] = useState(false)
  const [customName, setCustomName] = useState('')
  const [customUrl, setCustomUrl] = useState('')
  useEffect(() => { request<typeof fallbackIntegrations>('/integrations').then((remote) => { const remoteById = new Map(remote.map((item) => [item.id, item])); setItems(fallbackIntegrations.map((fallback) => ({ ...fallback, ...(remoteById.get(fallback.id) ?? {}) }))) }).catch(() => undefined) }, [])
  const toggle = async (id: string, connected: boolean) => { setItems((current) => current.map((item) => item.id === id ? { ...item, connected: !connected, status: !connected ? 'Connected' : 'Available' } : item)); try { await request(`/integrations/${id}`, { method: 'PATCH', body: JSON.stringify({ connected: !connected }) }) } catch { setItems((current) => current.map((item) => item.id === id ? { ...item, connected, status: connected ? 'Connected' : 'Available' } : item)) } }
  const visible = items.filter((item) => (filter === 'All' || item.kind === filter.slice(0, -1)) && (!searchQuery.trim() || `${item.name} ${item.category} ${item.description}`.toLowerCase().includes(searchQuery.toLowerCase())))
  const addCustom = (event: FormEvent) => { event.preventDefault(); if (!customName.trim() || !customUrl.trim()) return; setItems((current) => [...current, { id: `custom-${Date.now()}`, name: customName.trim(), kind: 'Application', category: 'Custom', description: customUrl.trim(), status: 'Connected', connected: true, logo: 'K' }]); setCustomName(''); setCustomUrl(''); setCustomOpen(false) }
  return <><div className="page-heading compact"><div><h1>Let Kloppy work<br />where work already happens.</h1><p className="heading-copy">Connect the tools and knowledge your agent can use to research, create, distribute, and learn. Access is scoped, visible, and always revocable.</p></div><div className="heading-actions"><button className="button secondary" onClick={() => setCustomOpen(!customOpen)}><Icon name="plus" size={15} /> Add custom</button><button className="button secondary"><Icon name="external" size={15} /> View connector docs</button></div></div>{customOpen && <form className="custom-connector" onSubmit={addCustom}><div><span className="section-kicker">In-house connector</span><h2>Connect a company-owned system.</h2><p>Add a private app, site, API, or internal resource to the connector directory.</p></div><label>Name<input value={customName} onChange={(event) => setCustomName(event.target.value)} placeholder="Oyin Fab inventory API" required /></label><label>URL<input type="url" value={customUrl} onChange={(event) => setCustomUrl(event.target.value)} placeholder="https://internal.example.com" required /></label><button className="button primary" type="submit">Save connection <Icon name="check" size={15} /></button></form>}<div className="connector-toolbar"><div className="filter-tabs">{(['All', 'Applications', 'Resources'] as const).map((option) => <button className={filter === option ? 'active' : ''} key={option} onClick={() => setFilter(option)}>{option}<span>{option === 'All' ? items.length : items.filter((item) => item.kind === option.slice(0, -1)).length}</span></button>)}</div></div><div className="connector-grid">{visible.length ? visible.map((item) => <article className="connector-card" key={item.id}><div className="connector-card-head"><div className={`connector-logo logo-${item.id}`}>{item.logo}</div><span className={`connector-status ${item.connected ? 'connected' : ''}`}><span />{item.connected ? 'Connected' : 'Available'}</span></div><span className="integration-category">{item.kind} · {item.category}</span><h2>{item.name}</h2><p>{item.description}</p><div className="connector-card-foot"><span className="connector-scope">{item.connected ? 'Read + draft access' : 'OAuth connection'}</span><button className={`button ${item.connected ? 'secondary' : 'primary'}`} onClick={() => void toggle(item.id, item.connected)}>{item.connected ? 'Manage' : 'Connect'}</button></div></article>) : <div className="connector-empty">No connectors match “{searchQuery}”. Try a provider, capability, or category.</div>}</div></>
}

function Settings() {
  const [profile, setProfile] = useState<UserSettings>({ name: '', workspace: '', digest_enabled: true, permission_policy: 'ask' })
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  useEffect(() => { request<UserSettings>('/settings').then(setProfile).catch((reason) => setError(reason instanceof Error ? reason.message : 'Could not load settings.')).finally(() => setLoading(false)) }, [])
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
  return <><div className="page-heading compact"><div><div className="heading-meta">Account settings</div><h1>Set the room<br />up for better work.</h1><p className="heading-copy">Control how Kloppy speaks, where your work lives, and which decisions need your approval.</p></div></div><form className="settings-layout" onSubmit={save}><section className="settings-section"><div><span className="section-kicker">Account identity</span><h2>How your team sees this space</h2><p>These details help Kloppy keep campaign language grounded in your world.</p></div><div className="settings-fields"><label>Your name<input required minLength={2} maxLength={80} value={profile.name} onChange={(event) => setProfile({ ...profile, name: event.target.value })} /></label><label>Organization name<input required minLength={2} maxLength={120} value={profile.workspace} onChange={(event) => setProfile({ ...profile, workspace: event.target.value })} /></label></div></section><section className="settings-section"><div><span className="section-kicker">Working style</span><h2>Keep the signal visible</h2><p>Drafting can happen quickly; publishing and spend always need clear approval.</p></div><div className="settings-fields"><label>Draft approval preference<select value={profile.permission_policy} onChange={(event) => setProfile({ ...profile, permission_policy: event.target.value as UserSettings['permission_policy'] })}><option value="ask">Ask before actions</option><option value="auto">Auto-run drafts</option></select></label><label className="toggle-row"><span><strong>Weekly campaign digest</strong><small>A short read on what changed and what deserves your attention.</small></span><input type="checkbox" checked={profile.digest_enabled} onChange={(event) => setProfile({ ...profile, digest_enabled: event.target.checked })} /><span className="toggle" /></label></div></section><div className="settings-footer"><span className="secure-note"><Icon name="lock" size={13} /> {loading ? 'Loading saved settings…' : error || 'Changes are saved privately.'}</span><button className="button primary" type="submit" disabled={loading}>{saved ? 'Saved' : 'Save changes'} <Icon name={saved ? 'check' : 'arrow'} size={15} /></button></div></form></>
}
function CampaignTabs({ page, setPage }: { page: Page; setPage: (page: Page) => void }) {
  return <nav className="campaign-tabs" aria-label="Campaign sections">{campaignNav.map((item) => <button aria-label={item.label} className={page === item.page ? 'active' : ''} key={item.page} onClick={() => setPage(item.page)}>{item.page === 'campaign-chat' ? <KloppyMark /> : <Icon name={item.icon} size={15} />}{item.page === 'campaign-chat' ? null : item.label}</button>)}</nav>
}

function App() {
  const initialRoute = window.location.hash.slice(1) || 'landing'
  const [route, setRoute] = useState(initialRoute === 'creative' ? 'campaign-chat' : initialRoute); const [authMode, setAuthMode] = useState<AuthMode>('login'); const [user, setUser] = useState({ name: 'Amara K.' }); const [data, setData] = useState(fallbackDashboard); const [searchQuery, setSearchQuery] = useState('')
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
  useEffect(() => { if (route === 'overview' || route === 'campaigns' || route === 'audience' || route === 'strategy' || route === 'launch' || route === 'integrations' || route === 'settings') request<typeof fallbackDashboard>('/dashboard').then(setData).catch(() => undefined) }, [route])
  const go = (next: string) => { window.location.hash = next }
  const logout = () => { localStorage.removeItem('kloppy-session'); setAuthMode('login'); go('landing') }
  if (route === 'landing') return <Landing onAuth={(mode) => { setAuthMode(mode); go('auth') }} />
  if (route === 'auth') return <Auth mode={authMode} onMode={setAuthMode} onComplete={(nextUser) => { setUser(nextUser); go('chat') }} />
  const pages: Page[] = ['chat', 'campaigns', 'knowledge', 'integrations', 'settings', 'campaign-chat', 'overview', 'audience', 'strategy', 'launch']
  const page = (pages.includes(route as Page) ? route : 'chat') as Page
  const pageTitle = page === 'chat' ? 'Kloppy' : page === 'knowledge' ? 'Knowledge' : ['campaign-chat', 'overview', 'audience', 'strategy', 'launch'].includes(page) ? campaignNav.find((item) => item.page === page)?.label ?? 'Campaign' : navItems.find((item) => item.page === page)?.label ?? page
  const hasStudio = ['campaign-chat', 'overview', 'audience', 'strategy', 'launch'].includes(page)
  const canSearch = page === 'campaigns' || page === 'integrations'
  return <div className="app-shell"><Sidebar page={page} setPage={(next) => go(next)} user={user} onLogout={logout} /><main className="main-content"><header className="topbar"><div className="breadcrumb"><span>Kloppy</span><Icon name="chevron" size={14} /><strong>{pageTitle}</strong></div>{canSearch && <div className="topbar-actions"><label className="search-control"><Icon name="search" size={17} /><input aria-label={`Search ${page}`} value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} placeholder={page === 'campaigns' ? 'Search campaigns' : 'Search connectors'} /><kbd>⌘ K</kbd></label></div>}</header>{hasStudio && <CampaignTabs page={page} setPage={(next) => go(next)} />}<div className={page === 'chat' || page === 'campaign-chat' ? 'chat-page-wrap' : 'page-wrap'}>{page === 'chat' ? <ChatPage /> : page === 'campaign-chat' ? <ChatPage campaign /> : null}{page === 'campaigns' && <StagePage page="campaigns" onAsk={() => go('campaign-chat')} onCampaignOpen={() => go('campaign-chat')} searchQuery={searchQuery} />}{page === 'knowledge' && <Knowledge />}{page === 'overview' && <Overview data={data} onNavigate={() => go('campaign-chat')} />}{['audience', 'strategy', 'launch'].includes(page) && <StagePage page={page as 'audience' | 'strategy' | 'launch'} onAsk={() => go('campaign-chat')} />}{page === 'integrations' && <Integrations searchQuery={searchQuery} />}{page === 'settings' && <Settings />}</div></main></div>
}

export default App
