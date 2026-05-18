#!/usr/bin/env python3
"""
AI Settings Templates — PDF generation and Google Drive upload.

Creates settings template PDFs for Claude, ChatGPT, and Gemini and uploads
them to their respective subfolders inside the existing 'AI' Google Drive folder.

Dependencies:
    pip install google-auth google-auth-oauthlib google-api-python-client reportlab
"""

import os
import io
from datetime import date

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)

# ─── Constants ────────────────────────────────────────────────────────────────

SCOPES = ['https://www.googleapis.com/auth/drive']
MARGIN = 1.8 * cm
PAGE_W, PAGE_H = A4

# ─── AI Template definitions ──────────────────────────────────────────────────

TEMPLATES = {
    'Claude': {
        'accent_hex': '#D97706',
        'bg_hex':     '#FFF7ED',
        'sections': [
            {
                'title': 'General Settings',
                'settings': [
                    ('Model',
                     'Claude model version to use',
                     'claude-opus-4-7 / claude-sonnet-4-6 / claude-haiku-4-5'),
                    ('Temperature',
                     'Randomness — 0.0 = deterministic, 1.0 = most creative',
                     '0.7'),
                    ('Max Tokens',
                     'Hard ceiling on output tokens per response',
                     '4096'),
                    ('Top P',
                     'Nucleus sampling; lower = more focused',
                     '1.0'),
                ],
            },
            {
                'title': 'Memory & Context Settings',
                'settings': [
                    ('Context Window',
                     'Maximum input context used per API call',
                     '200K tokens'),
                    ('Conversation History',
                     'Number of past turns to include in each call',
                     '10'),
                    ('System Prompt',
                     'Persistent instructions prepended to every conversation',
                     ''),
                    ('Prompt Caching',
                     'Cache repeated prompt prefixes to cut cost & latency',
                     'Enabled / Disabled'),
                    ('Memory Mode',
                     'Cross-session persistence strategy',
                     'File-based / None'),
                ],
            },
            {
                'title': 'Tool Settings',
                'settings': [
                    ('Tool Use Mode',
                     'Controls when tools may be invoked',
                     'auto / any / tool'),
                    ('Available Tools',
                     'Comma-separated list of enabled tool/function names',
                     ''),
                    ('Computer Use',
                     'Allow Claude to control mouse and keyboard',
                     'Enabled / Disabled'),
                    ('Bash Execution',
                     'Allow shell command execution in a sandbox',
                     'Enabled / Disabled'),
                    ('Web Search',
                     'Allow real-time web search results',
                     'Enabled / Disabled'),
                    ('File Access',
                     'Allow reading and writing local files',
                     'Enabled / Disabled'),
                ],
            },
            {
                'title': 'Output & Format Settings',
                'settings': [
                    ('Response Format',
                     'Preferred output style',
                     'Markdown / Plain Text / JSON'),
                    ('Stream Output',
                     'Receive tokens as they are generated',
                     'Enabled / Disabled'),
                    ('Stop Sequences',
                     'Strings that halt generation when encountered',
                     ''),
                    ('Language',
                     'Preferred response language',
                     'English'),
                ],
            },
            {
                'title': 'Safety & Compliance Settings',
                'settings': [
                    ('Content Filtering',
                     'Anthropic built-in safety moderation level',
                     'Default'),
                    ('Sensitive Topics',
                     'Subjects to refuse, flag, or handle with care',
                     ''),
                    ('Data Retention',
                     'Whether conversations are stored by Anthropic',
                     'Per Anthropic policy'),
                    ('API Key Rotation',
                     'How often the API key should be cycled',
                     'Every 90 days'),
                ],
            },
        ],
    },

    'ChatGPT': {
        'accent_hex': '#10A37F',
        'bg_hex':     '#F0FDF4',
        'sections': [
            {
                'title': 'General Settings',
                'settings': [
                    ('Model',
                     'GPT model version to use',
                     'gpt-4o / gpt-4-turbo / gpt-3.5-turbo'),
                    ('Temperature',
                     'Randomness level (0.0–2.0)',
                     '1.0'),
                    ('Max Tokens',
                     'Hard ceiling on output tokens per response',
                     '4096'),
                    ('Top P',
                     'Nucleus sampling threshold',
                     '1.0'),
                    ('Frequency Penalty',
                     'Penalise token repetition (-2.0 to 2.0)',
                     '0.0'),
                    ('Presence Penalty',
                     'Encourage new topic coverage (-2.0 to 2.0)',
                     '0.0'),
                ],
            },
            {
                'title': 'Memory Settings',
                'settings': [
                    ('Memory Enabled',
                     'Persist user facts across separate conversations',
                     'Enabled / Disabled'),
                    ('Custom Instructions',
                     'Persistent background context and preferences',
                     ''),
                    ('Conversation History',
                     'Number of past turns to include in each call',
                     '10'),
                    ('Memory Scope',
                     'Categories of information to remember',
                     'Facts / Preferences / Both'),
                ],
            },
            {
                'title': 'Security Settings',
                'settings': [
                    ('Content Policy',
                     'OpenAI moderation enforcement level',
                     'Default'),
                    ('Data Sharing',
                     'Allow OpenAI to use your data for model training',
                     'Enabled / Disabled'),
                    ('API Key Rotation',
                     'How often the API key should be cycled',
                     'Every 90 days'),
                    ('Monthly Spend Limit',
                     'Hard cap on monthly API spend (USD)',
                     ''),
                    ('IP Restrictions',
                     'Allowlisted source IPs for API access',
                     ''),
                    ('Org / Project Scope',
                     'Restrict key to a specific organisation or project',
                     ''),
                ],
            },
            {
                'title': 'Tool & Plugin Settings',
                'settings': [
                    ('Function Calling',
                     'Control when functions/tools may be invoked',
                     'auto / required / none'),
                    ('Code Interpreter',
                     'Python sandbox execution inside the model',
                     'Enabled / Disabled'),
                    ('Web Search',
                     'Real-time browsing grounding for responses',
                     'Enabled / Disabled'),
                    ('File Upload',
                     'Read and analyse user-uploaded files',
                     'Enabled / Disabled'),
                    ('DALL-E Image Gen',
                     'Generate images via DALL-E alongside text',
                     'Enabled / Disabled'),
                    ('Custom Plugins',
                     'Comma-separated list of third-party plugins',
                     ''),
                ],
            },
            {
                'title': 'Output & Format Settings',
                'settings': [
                    ('Response Format',
                     'Output structure type',
                     'text / json_object / json_schema'),
                    ('Stream Output',
                     'Receive tokens as they are generated',
                     'Enabled / Disabled'),
                    ('Stop Sequences',
                     'Strings that halt generation when encountered',
                     ''),
                    ('Language',
                     'Preferred response language',
                     'English'),
                ],
            },
        ],
    },

    'Gemini': {
        'accent_hex': '#4285F4',
        'bg_hex':     '#EFF6FF',
        'sections': [
            {
                'title': 'General Settings',
                'settings': [
                    ('Model',
                     'Gemini model version to use',
                     'gemini-2.0-flash / gemini-1.5-pro / gemini-1.5-flash'),
                    ('Temperature',
                     'Randomness level (0.0–2.0)',
                     '1.0'),
                    ('Max Output Tokens',
                     'Hard ceiling on output tokens per response',
                     '8192'),
                    ('Top P',
                     'Nucleus sampling threshold',
                     '0.95'),
                    ('Top K',
                     'Top-K sampling — limits candidate token pool',
                     '40'),
                    ('Candidate Count',
                     'Number of response candidates to generate',
                     '1'),
                ],
            },
            {
                'title': 'Safety Settings',
                'settings': [
                    ('Harassment Filter',
                     'Block level for harassment content',
                     'BLOCK_MEDIUM_AND_ABOVE'),
                    ('Hate Speech Filter',
                     'Block level for hate speech',
                     'BLOCK_MEDIUM_AND_ABOVE'),
                    ('Sexually Explicit Filter',
                     'Block level for sexually explicit content',
                     'BLOCK_MEDIUM_AND_ABOVE'),
                    ('Dangerous Content Filter',
                     'Block level for dangerous or harmful content',
                     'BLOCK_MEDIUM_AND_ABOVE'),
                    ('Civic Integrity Filter',
                     'Block level for civic integrity violations',
                     'BLOCK_MEDIUM_AND_ABOVE'),
                ],
            },
            {
                'title': 'Memory & Context Settings',
                'settings': [
                    ('Context Window',
                     'Maximum input context used per API call',
                     '1M tokens'),
                    ('System Instruction',
                     'Persistent instructions prepended to every conversation',
                     ''),
                    ('Conversation History',
                     'Number of past turns to include in each call',
                     '10'),
                    ('Context Caching',
                     'Cache large repeated context to cut latency & cost',
                     'Enabled / Disabled'),
                ],
            },
            {
                'title': 'Tool & Extension Settings',
                'settings': [
                    ('Google Search Grounding',
                     'Ground answers with real-time Google Search results',
                     'Enabled / Disabled'),
                    ('Code Execution',
                     'Python sandbox execution inside the model',
                     'Enabled / Disabled'),
                    ('Function Calling Mode',
                     'Control when functions/tools may be invoked',
                     'AUTO / ANY / NONE'),
                    ('Google Workspace',
                     'Access Gmail, Drive, Docs, Sheets, etc.',
                     'Enabled / Disabled'),
                    ('YouTube Extension',
                     'Access and analyse YouTube video content',
                     'Enabled / Disabled'),
                ],
            },
            {
                'title': 'Output & Format Settings',
                'settings': [
                    ('Response MIME Type',
                     'Output format type',
                     'text/plain / application/json'),
                    ('Response Schema',
                     'JSON schema definition for structured output',
                     ''),
                    ('Stream Output',
                     'Receive tokens as they are generated',
                     'Enabled / Disabled'),
                    ('Stop Sequences',
                     'Strings that halt generation when encountered',
                     ''),
                    ('Language',
                     'Preferred response language',
                     'English'),
                ],
            },
        ],
    },
}

# ─── PDF helpers ──────────────────────────────────────────────────────────────

def _build_styles(accent: colors.Color, bg: colors.Color):
    base = getSampleStyleSheet()
    return {
        'title': ParagraphStyle(
            'ai_title', parent=base['Title'],
            fontSize=22, leading=28, textColor=accent, spaceAfter=4,
        ),
        'subtitle': ParagraphStyle(
            'ai_subtitle', parent=base['Normal'],
            fontSize=10, leading=14, textColor=colors.HexColor('#555555'),
        ),
        'section_hdr': ParagraphStyle(
            'ai_section_hdr', parent=base['Normal'],
            fontSize=11, leading=16, textColor=colors.white,
        ),
        'col_hdr': ParagraphStyle(
            'ai_col_hdr', parent=base['Normal'],
            fontSize=8, leading=11, textColor=colors.HexColor('#374151'),
        ),
        'cell_name': ParagraphStyle(
            'ai_cell_name', parent=base['Normal'],
            fontSize=9, leading=12, textColor=colors.HexColor('#111827'),
        ),
        'cell_desc': ParagraphStyle(
            'ai_cell_desc', parent=base['Normal'],
            fontSize=8, leading=11, textColor=colors.HexColor('#6B7280'),
        ),
        'cell_opt': ParagraphStyle(
            'ai_cell_opt', parent=base['Normal'],
            fontSize=8, leading=11, textColor=colors.HexColor('#2563EB'),
        ),
        'instructions': ParagraphStyle(
            'ai_instructions', parent=base['Normal'],
            fontSize=8, leading=12, textColor=colors.HexColor('#374151'),
        ),
        'instructions_hdr': ParagraphStyle(
            'ai_instructions_hdr', parent=base['Normal'],
            fontSize=9, leading=13, textColor=colors.HexColor('#111827'),
        ),
        'footer': ParagraphStyle(
            'ai_footer', parent=base['Normal'],
            fontSize=7, leading=10, textColor=colors.HexColor('#9CA3AF'),
            alignment=TA_CENTER,
        ),
        '_accent': accent,
        '_bg':     bg,
    }


def _section_block(title: str, rows: list, st: dict) -> KeepTogether:
    accent = st['_accent']
    col_w = [4.2 * cm, 7.8 * cm, 4.4 * cm, 3.6 * cm]

    # Section title bar
    hdr_tbl = Table(
        [[Paragraph(title, st['section_hdr']), '', '', '']],
        colWidths=col_w,
    )
    hdr_tbl.setStyle(TableStyle([
        ('SPAN',          (0, 0), (3, 0)),
        ('BACKGROUND',    (0, 0), (3, 0), accent),
        ('TOPPADDING',    (0, 0), (3, 0), 7),
        ('BOTTOMPADDING', (0, 0), (3, 0), 7),
        ('LEFTPADDING',   (0, 0), (3, 0), 8),
    ]))

    # Column header + data rows
    col_headers = [
        Paragraph('<b>Setting</b>',          st['col_hdr']),
        Paragraph('<b>Description</b>',      st['col_hdr']),
        Paragraph('<b>Default / Options</b>', st['col_hdr']),
        Paragraph('<b>Your Value</b>',        st['col_hdr']),
    ]
    table_data = [col_headers]
    for name, desc, opts in rows:
        table_data.append([
            Paragraph(f'<b>{name}</b>', st['cell_name']),
            Paragraph(desc,             st['cell_desc']),
            Paragraph(opts,             st['cell_opt']),
            '',   # intentionally blank — user fills in
        ])

    stripe_rules = []
    for i in range(len(table_data)):
        bg = colors.HexColor('#F9FAFB') if i % 2 == 0 else colors.white
        stripe_rules.append(('BACKGROUND', (0, i), (3, i), bg))

    data_tbl = Table(table_data, colWidths=col_w)
    data_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (3, 0), colors.HexColor('#F3F4F6')),
        ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 6),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ] + stripe_rules))

    return KeepTogether([hdr_tbl, data_tbl, Spacer(1, 0.45 * cm)])


def generate_pdf(ai_name: str, config: dict) -> bytes:
    accent = colors.HexColor(config['accent_hex'])
    bg     = colors.HexColor(config['bg_hex'])
    st     = _build_styles(accent, bg)
    buf    = io.BytesIO()

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
        title=f'{ai_name} — Settings Template',
        author='AI Settings Template Generator',
    )

    story = []

    # Title
    story.append(Paragraph(f'{ai_name} — Settings Template', st['title']))
    story.append(Paragraph(
        f'Generated: {date.today().isoformat()}',
        st['subtitle'],
    ))
    story.append(HRFlowable(width='100%', thickness=2, color=accent, spaceAfter=8))
    story.append(Spacer(1, 0.25 * cm))

    # How-to banner
    instructions_tbl = Table(
        [[
            Paragraph('<b>How to use this template</b>', st['instructions_hdr']),
            Paragraph(
                '1. Review each setting name and description.<br/>'
                '2. Pick a value from <font color="#2563EB">Default / Options</font> '
                'or enter your own.<br/>'
                '3. Write your chosen value in the <b>Your Value</b> column.<br/>'
                '4. Apply the values in your API call, SDK config, or AI dashboard.',
                st['instructions'],
            ),
        ]],
        colWidths=[3.8 * cm, 16.2 * cm],
    )
    instructions_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), bg),
        ('BOX',           (0, 0), (-1, -1), 1.2, accent),
        ('TOPPADDING',    (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(instructions_tbl)
    story.append(Spacer(1, 0.5 * cm))

    # Sections
    for section in config['sections']:
        story.append(_section_block(section['title'], section['settings'], st))

    # Footer
    story.append(Spacer(1, 0.2 * cm))
    story.append(HRFlowable(
        width='100%', thickness=0.5,
        color=colors.HexColor('#D1D5DB'), spaceAfter=4,
    ))
    story.append(Paragraph(
        f'{ai_name} Settings Template  ·  {date.today().isoformat()}  ·  '
        'For internal use — update values as models and APIs evolve.',
        st['footer'],
    ))

    doc.build(story)
    return buf.getvalue()


# ─── Google Drive helpers ─────────────────────────────────────────────────────

def authenticate():
    from google.auth.exceptions import RefreshError

    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                # Refresh token is revoked or expired — delete and re-authenticate
                print('   WARN — Stored token is invalid; starting fresh login...')
                os.remove('token.json')
                creds = None

        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as fh:
            fh.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)


def find_folder(service, name: str, parent_id: str = None) -> str | None:
    """Return the Drive ID of the first folder matching name, or None."""
    q = (
        f"name='{name}' "
        "and mimeType='application/vnd.google-apps.folder' "
        "and trashed=false"
    )
    if parent_id:
        q += f" and '{parent_id}' in parents"
    results = service.files().list(q=q, fields='files(id, name)').execute()
    files = results.get('files', [])
    return files[0]['id'] if files else None


def upload_pdf(service, pdf_bytes: bytes, filename: str, folder_id: str) -> dict:
    """Upload pdf_bytes as filename into folder_id; return the created file metadata."""
    media = MediaIoBaseUpload(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        resumable=False,
    )
    metadata = {'name': filename, 'parents': [folder_id]}
    return service.files().create(
        body=metadata, media_body=media, fields='id, name',
    ).execute()


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print('=' * 70)
    print('AI SETTINGS TEMPLATES — PDF GENERATION & UPLOAD')
    print('=' * 70)

    # Auth
    print('\nAuthenticating with Google Drive...')
    service = authenticate()
    print('OK — Authentication successful')

    # Locate the parent AI folder
    ai_folder_id = find_folder(service, 'AI')
    if not ai_folder_id:
        print('ERROR — "AI" folder not found in Google Drive.')
        print('        Run create_ai_folders.py first to create the folder structure.')
        return
    print(f'OK — Found AI folder  (ID: {ai_folder_id})')

    # Map AI name → subfolder name (as created by create_ai_folders.py)
    subfolder_map = {
        'Claude':   'Claude',
        'ChatGPT':  'ChatGPT',
        'Gemini':   'Gemini',
    }

    print()
    for ai_name, folder_name in subfolder_map.items():
        print(f'── {ai_name} ─────────────────────────────────────────')

        # Find subfolder
        subfolder_id = find_folder(service, folder_name, parent_id=ai_folder_id)
        if not subfolder_id:
            print(f'   WARN — "{folder_name}" subfolder not found; skipping.')
            continue
        print(f'   OK — Found subfolder "{folder_name}"  (ID: {subfolder_id})')

        # Generate PDF
        print(f'   Generating PDF...')
        pdf_bytes = generate_pdf(ai_name, TEMPLATES[ai_name])
        print(f'   OK — PDF generated  ({len(pdf_bytes):,} bytes)')

        # Upload
        filename = f'{ai_name}_Settings_Template_{date.today().isoformat()}.pdf'
        print(f'   Uploading "{filename}"...')
        result = upload_pdf(service, pdf_bytes, filename, subfolder_id)
        print(f'   OK — Uploaded  (File ID: {result["id"]})')
        print()

    print('=' * 70)
    print('ALL TEMPLATES UPLOADED SUCCESSFULLY')
    print('=' * 70)
    print()
    print('Folder structure in Google Drive:')
    print('  AI/')
    for folder_name in subfolder_map.values():
        print(f'    ├─ {folder_name}/')
        print(f'    │    └─ {folder_name}_Settings_Template_{date.today().isoformat()}.pdf')
    print('=' * 70)


if __name__ == '__main__':
    main()
