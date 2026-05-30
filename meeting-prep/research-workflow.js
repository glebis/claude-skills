export const meta = {
  name: 'meeting-prep-research',
  description: 'Research meeting participants in parallel and compile prep notes',
  phases: [
    { title: 'Research', detail: 'Web research + vault history per participant' },
    { title: 'Verify', detail: 'Cross-check research claims for accuracy' },
    { title: 'Compile', detail: 'Create prep notes in Obsidian vault' }
  ]
}

const RESEARCH_SCHEMA = {
  type: 'object',
  properties: {
    name: { type: 'string' },
    email: { type: 'string' },
    role: { type: 'string', description: 'Current role and company' },
    company_context: { type: 'string', description: 'What the company does, size, recent news' },
    linkedin_summary: { type: 'string', description: 'Career highlights, expertise areas' },
    mutual_context: { type: 'string', description: 'Shared connections, projects, or context with the meeting host' },
    conversation_starters: {
      type: 'array',
      items: { type: 'string' },
      description: '2-3 relevant conversation starters'
    },
    session_count: { type: 'number', description: 'Number of previous sessions found in vault' },
    previous_sessions: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          date: { type: 'string' },
          title: { type: 'string' },
          duration: { type: 'string' },
          key_topics: { type: 'array', items: { type: 'string' } },
          action_items: { type: 'array', items: { type: 'string' } },
          source: { type: 'string' }
        }
      }
    },
    recurring_themes: { type: 'array', items: { type: 'string' } },
    outstanding_followups: { type: 'array', items: { type: 'string' } }
  },
  required: ['name', 'role', 'session_count']
}

const VERIFY_SCHEMA = {
  type: 'object',
  properties: {
    name: { type: 'string' },
    email_domain_match: { type: 'boolean', description: 'Does the claimed company match the email domain?' },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'], description: 'Overall confidence in research accuracy' },
    flags: {
      type: 'array',
      items: { type: 'string' },
      description: 'Suspicious or unverifiable claims'
    },
    verified_role: { type: 'string', description: 'Verified or best-guess role' },
    verified_company: { type: 'string', description: 'Verified or best-guess company' }
  },
  required: ['name', 'email_domain_match', 'confidence', 'flags', 'verified_role', 'verified_company']
}

// Parse args — comes as string from Workflow tool
const parsedArgs = typeof args === 'string' ? JSON.parse(args) : (args || {})
const bookings = parsedArgs.bookings || []
const config = parsedArgs.config || {}

// Config-driven paths (passed by the skill, read from config.yaml)
if (!config.meetings_dir || !config.vault_root) {
  throw new Error('config.meetings_dir and config.vault_root are required — pass them from config.yaml via workflow args')
}
const MEETINGS_DIR = config.meetings_dir
const VAULT_ROOT = config.vault_root
const PEOPLE_DEPTH = config.people_search_depth || 2
const PREP_PREFIX = config.prep_prefix || 'prep'
const TYPE_TAG = config.type_tag || 'meeting-prep'
const TIMEZONE = config.timezone || 'UTC'
const HOST_NAME = config.host_name || 'the meeting host'
const HOST_ROLE = config.host_role || ''
const HOST_LOCATION = config.host_location || ''

// Normalize attendees: each booking may have a single participant (name+email)
// or an attendees array [{name, email, timezone}, ...] for group sessions.
for (const b of bookings) {
  if (!b.attendees || b.attendees.length === 0) {
    b.attendees = [{ name: b.participant, email: b.email, timezone: b.timezone }]
  }
}

const uniqueParticipants = []
const seenEmails = new Set()
for (const b of bookings) {
  for (const att of b.attendees) {
    if (!seenEmails.has(att.email)) {
      seenEmails.add(att.email)
      uniqueParticipants.push({ name: att.name, email: att.email })
    }
  }
}

log('Preparing ' + bookings.length + ' sessions for ' + uniqueParticipants.length + ' unique participants')

phase('Research')

const researchAndVerify = await parallel(
  uniqueParticipants.map((p) => () =>
    pipeline([
      () => agent(
        'Research this person AND search the Obsidian vault for previous session history.\n\n' +
        'PERSON:\n' +
        'Name: ' + p.name + '\n' +
        'Email: ' + p.email + '\n' +
        'Email domain: ' + p.email.split('@')[1] + '\n\n' +
        'PART 1 — WEB RESEARCH:\n' +
        'Search the web for their name + company/domain. Check LinkedIn.' + (HOST_LOCATION ? ' Look for connections to the ' + HOST_LOCATION + ' tech scene.' : '') + ' The meeting host is ' + HOST_NAME + (HOST_ROLE ? ', ' + HOST_ROLE : '') + (HOST_LOCATION ? ' in ' + HOST_LOCATION : '') + '.\n\n' +
        'PART 2 — VAULT HISTORY:\n' +
        'Search for previous meeting notes in ' + MEETINGS_DIR + '\n' +
        '1. Run: grep -rl "' + p.name + '" ' + MEETINGS_DIR + ' 2>/dev/null\n' +
        '2. Also try first name only: grep -rl "' + p.name.split(' ')[0] + '" ' + MEETINGS_DIR + ' 2>/dev/null\n' +
        '3. Read matching files (up to 5 most recent by date prefix) and extract: date, duration, key topics, action items, source (fathom/granola/manual)\n' +
        '4. Also check: find ' + VAULT_ROOT + ' -maxdepth ' + PEOPLE_DEPTH + ' -name "*' + (p.name.split(' ')[1] || p.name.split(' ')[0]) + '*" -not -path "*/Meetings/*" 2>/dev/null\n\n' +
        'Return everything in the structured schema. If no previous sessions found, set session_count to 0. Do not fabricate information.',
        { label: 'profile:' + p.name, phase: 'Research', schema: RESEARCH_SCHEMA }
      ),
      (profile) => {
        if (!profile || !profile.role) return { profile, verification: null }
        const domain = p.email.split('@')[1]
        return agent(
          'Verify the accuracy of this research profile. Cross-check claims against the email domain and look for red flags.\n\n' +
          'PERSON: ' + p.name + '\n' +
          'EMAIL DOMAIN: ' + domain + '\n\n' +
          'RESEARCH PROFILE:\n' + JSON.stringify(profile, null, 2) + '\n\n' +
          'CHECK THE FOLLOWING:\n' +
          '1. Does the claimed company match the email domain "' + domain + '"? For example, if the domain is "all3.com" the company should be All3 or a known subsidiary/brand. Set email_domain_match accordingly.\n' +
          '2. Are there claims that seem implausible or could be confused with a different person of the same name? List each suspicious claim in "flags".\n' +
          '3. Assign a confidence level (high/medium/low) for the overall profile. Use "low" if the company doesn\'t match the domain or multiple claims look wrong. Use "medium" if there are minor uncertainties. Use "high" if everything checks out.\n' +
          '4. Provide verified_role and verified_company with your best understanding of their actual role and company.\n\n' +
          'Return the structured verification result.',
          { label: 'verify:' + p.name, phase: 'Verify', schema: VERIFY_SCHEMA }
        ).then((v) => ({ profile, verification: v }))
      }
    ])
  )
)

phase('Verify')

const profileByEmail = {}
for (let i = 0; i < uniqueParticipants.length; i++) {
  const result = researchAndVerify[i]
  if (result && result.profile) {
    const profile = result.profile
    const v = result.verification
    if (v) {
      profile.research_confidence = v.confidence || 'medium'
      profile.research_flags = v.flags || []
      if (v.verified_role) profile.role = v.verified_role
      if (v.verified_company) profile.company_context = v.verified_company + (profile.company_context ? ' — ' + profile.company_context : '')
    } else {
      profile.research_confidence = 'medium'
      profile.research_flags = ['Verification skipped — insufficient research data']
    }
    profileByEmail[uniqueParticipants[i].email] = profile
  }
}

log('Research & verification complete. Creating ' + bookings.length + ' prep notes.')

phase('Compile')

// Sort bookings by date so earlier sessions are processed first
const sortedBookings = [...bookings].sort((a, b) => a.date.localeCompare(b.date))

// Track prior prep notes per participant (by email) for sequential booking handling
const priorPrepByEmail = {}

const prepResults = await parallel(
  sortedBookings.map((booking) => () => {
    const isGroup = booking.attendees.length > 1
    const dateSlug = booking.date.replace(/-/g, '')

    if (isGroup) {
      // --- Group session: one note for all attendees ---
      const eventSlug = (booking.event_type_slug || booking.event_type).toLowerCase().replace(/\s+/g, '-')
      const filePath = MEETINGS_DIR + '/' + dateSlug + '-' + PREP_PREFIX + '-' + eventSlug + '.md'

      const attendeeProfiles = booking.attendees.map((att) => ({
        ...att,
        profile: profileByEmail[att.email] || {}
      }))

      const attendeeYaml = booking.attendees.map((att) =>
        '  - name: "' + att.name + '"\n    email: ' + att.email
      ).join('\n')

      const attendeeSections = attendeeProfiles.map((att) => {
        const p = att.profile
        const hasHistory = p.session_count && p.session_count > 0
        return '### ' + att.name + '\n' +
          'Summarize research: role, company, relevant context.\n' +
          'PROFILE: ' + JSON.stringify(p, null, 2) + '\n' +
          (hasHistory
            ? 'Previous sessions: ' + p.session_count + '. Summarize key topics and continuity.\n'
            : 'First-time participant — no vault history.\n')
      }).join('\n')

      return agent(
        'Create a GROUP meeting prep note as a markdown file.\n\n' +
        'WRITE THIS FILE: ' + filePath + '\n\n' +
        'BOOKING:\n' +
        '- Event type: ' + booking.event_type + '\n' +
        '- Date: ' + booking.date + '\n' +
        '- Time: ' + booking.time_cet + ' ' + TIMEZONE + '\n' +
        '- Duration: ' + booking.duration + ' min\n' +
        '- Zoom: ' + (booking.zoom_link || 'TBD') + '\n' +
        '- Attendees: ' + booking.attendees.length + '\n\n' +
        'ALL ATTENDEE PROFILES:\n' + JSON.stringify(attendeeProfiles.map((a) => ({ name: a.name, email: a.email, profile: a.profile })), null, 2) + '\n\n' +
        'TEMPLATE:\n' +
        '---\n' +
        'type: ' + TYPE_TAG + '\n' +
        'date: ' + booking.date + '\n' +
        'participants:\n' + attendeeYaml + '\n' +
        'event_type: "' + booking.event_type + '"\n' +
        'duration: ' + booking.duration + '\n' +
        'time: "' + booking.time_cet + '"\n' +
        'status: prep\n' +
        'session_note: ""\n' +
        'tags:\n  - ' + TYPE_TAG + '\n' +
        '---\n\n' +
        '# Prep: ' + booking.event_type + ' — ' + booking.date + '\n\n' +
        '## Session Info\n' +
        'Fill in time, type, location. Use ' + TIMEZONE + ' for display.\n' +
        'Attendees: ' + booking.attendees.length + ' participants.\n\n' +
        '## Attendees\n\n' +
        attendeeSections + '\n' +
        '## Previous Sessions per Attendee\n' +
        'Summarize vault history grouped by person. Skip attendees with no history.\n\n' +
        '## Prep Ideas\n' +
        '- Group dynamics to consider\n' +
        '- Topics to cover with the full group\n' +
        '- Individual follow-ups to weave in\n\n' +
        '## Notes\n' +
        '_Space for pre-meeting thoughts_\n\n' +
        'IMPORTANT: Write the actual file using the Write tool. Fill in real content from the profile data, do not leave placeholders. Return the file path when done.',
        { label: 'note:' + booking.event_type + ' (' + booking.date + ', ' + booking.attendees.length + ' attendees)', phase: 'Compile' }
      )
    } else {
      // --- Solo session: one note per participant ---
      const profile = profileByEmail[booking.attendees[0].email] || {}
      const participant = booking.attendees[0].name || booking.participant
      const nameSlug = participant.toLowerCase().replace(/\s+/g, '-')
      const filePath = MEETINGS_DIR + '/' + dateSlug + '-' + PREP_PREFIX + '-' + nameSlug + '.md'

      const hasHistory = profile.session_count && profile.session_count > 0
      const lowConfidence = profile.research_confidence === 'low'
      const researchFlags = profile.research_flags || []

      // Check if this participant already has an earlier prep note in this batch
      const prior = priorPrepByEmail[booking.attendees[0].email]
      // Record this booking as the latest prep for this participant
      priorPrepByEmail[booking.attendees[0].email] = { path: filePath, date: booking.date, slug: dateSlug + '-' + PREP_PREFIX + '-' + nameSlug }

      const priorPrepInstruction = prior
        ? '\nSEQUENTIAL BOOKING — This participant has an earlier session on ' + prior.date + '.\n' +
          'After ## Session Info, add a ## Prior Session section:\n' +
          '  "A session with ' + participant.split(' ')[0] + ' is scheduled for ' + prior.date + ' — it will have happened by the time this session occurs.\n' +
          '  Update this note after the ' + prior.date + ' session with fresh context."\n' +
          'Keep all research/history sections but add a note: "(will be stale after ' + prior.date + ')"\n\n'
        : ''

      return agent(
        'Create a meeting prep note as a markdown file.\n\n' +
        'WRITE THIS FILE: ' + filePath + '\n\n' +
        priorPrepInstruction +
        'BOOKING:\n' +
        '- Participant: ' + participant + '\n' +
        '- Email: ' + booking.attendees[0].email + '\n' +
        '- Date: ' + booking.date + '\n' +
        '- Time: ' + booking.time_cet + ' ' + TIMEZONE + '\n' +
        '- Duration: ' + booking.duration + ' min\n' +
        '- Event type: ' + booking.event_type + '\n' +
        '- Zoom: ' + (booking.zoom_link || 'TBD') + '\n' +
        '- Participant timezone: ' + (booking.attendees[0].timezone || booking.timezone) + '\n\n' +
        'PROFILE & RESEARCH:\n' + JSON.stringify(profile, null, 2) + '\n\n' +
        'TEMPLATE:\n' +
        '---\n' +
        'type: ' + TYPE_TAG + '\n' +
        'date: ' + booking.date + '\n' +
        'participant: "' + participant + '"\n' +
        'email: ' + booking.attendees[0].email + '\n' +
        'event_type: "' + booking.event_type + '"\n' +
        'duration: ' + booking.duration + '\n' +
        'time: "' + booking.time_cet + '"\n' +
        (prior ? 'prior_prep: "[[' + prior.slug + ']]"\n' : '') +
        'status: prep\n' +
        'session_note: ""\n' +
        'tags:\n  - ' + TYPE_TAG + '\n' +
        '---\n\n' +
        '# Prep: ' + participant + ' — ' + booking.date + '\n\n' +
        (lowConfidence
          ? '> [!warning]\n> Research confidence is low — verify key facts before the meeting.\n' +
            (researchFlags.length > 0 ? '> Flags: ' + researchFlags.join('; ') + '\n' : '') + '\n'
          : (researchFlags.length > 0
              ? '> [!note] Research flags\n> ' + researchFlags.join('; ') + '\n\n'
              : '')) +
        '## Session Info\n' +
        'Fill in time, type, location, timezone. Use ' + TIMEZONE + ' for display.\n\n' +
        (prior
          ? '## Prior Session\n' +
            'A session with ' + participant.split(' ')[0] + ' is scheduled for ' + prior.date + ' — it will have happened by the time this session occurs.\n' +
            'Update this note after the ' + prior.date + ' session with fresh context.\n\n'
          : '') +
        '## About ' + participant.split(' ')[0] + '\n' +
        'Summarize research: role, company, relevant context. Keep concise.\n\n' +
        (hasHistory
          ? '## Previous Sessions (' + profile.session_count + ' total)' + (prior ? ' _(will be stale after ' + prior.date + ')_' : '') + '\n' +
            'Summarize the most recent sessions with dates, topics, outcomes.\n' +
            'Use data from profile.previous_sessions.\n\n' +
            '## Continuity & Follow-ups' + (prior ? ' _(will be stale after ' + prior.date + ')_' : '') + '\n' +
            'List outstanding action items, recurring themes, progress.\n' +
            'Use profile.outstanding_followups and profile.recurring_themes.\n\n'
          : '## First Meeting\nNo previous sessions found in vault.\n\n' +
            '## Context & Talking Points\n' +
            'Research-based starters, questions to understand their goals.\n\n') +
        '## Prep Ideas\n' +
        '- Conversation starters (use profile.conversation_starters)\n' +
        '- Topics to explore\n' +
        '- Questions to ask\n\n' +
        '## Notes\n' +
        '_Space for pre-meeting thoughts_\n\n' +
        'IMPORTANT: Write the actual file using the Write tool. Fill in real content from the profile data, do not leave placeholders. Return the file path when done.',
        { label: 'note:' + participant + ' (' + booking.date + ')', phase: 'Compile' }
      )
    }
  })
)

return {
  bookings_prepped: bookings.length,
  participants_researched: uniqueParticipants.length,
  prep_notes: prepResults.filter(Boolean)
}
