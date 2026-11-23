# Obsidian Chat-First Integration

## Status

Implemented. The integration uses the **Local REST API with MCP** Obsidian
community plugin. Vault access is executed by the BuddyAI backend; API keys and
TLS settings remain server-side.

## Approved user flow

1. The user selects an Obsidian tool in the chat composer.
2. The user enters a normal prompt describing the desired result.
3. BuddyAI optionally supplies chat context and, for existing-note operations,
   the target note content to the selected chat model.
4. The model generates Markdown and a typed proposal.
5. BuddyAI validates the action, path, allowed folder, permissions, and note
   version.
6. The draft appears in chat and can be edited.
7. The user confirms or cancels.
8. BuddyAI calls the Obsidian REST API.
9. The result is shown in chat.

The model does not receive or handle the Obsidian API key and does not execute
vault operations directly.

## Composer tools

- **Add a new note**
- **Search vault**
- **Read/open note**
- **Append to note**
- **Edit note section**
- **Replace note**
- **Delete note**

Tool selection is chat context, not an action form. Tools such as
`new_note` and `search` need no target path; tools acting on existing notes
provide a note path, and append/edit can provide a heading.

Examples:

```text
Create a SQLite notes summary from this conversation.
Search my vault for authentication decisions.
Append these decisions to the Decisions section of Projects/Meeting.md.
Replace the Summary section of Projects/Meeting.md.
Read Projects/Meeting.md.
Delete the obsolete draft at BuddyAI/Draft.md.
```

## Search and read behavior

Search is a direct REST operation and does not require an AI model call.
Search results include matching paths and excerpts. Selecting or reading a
result uses the REST read endpoint.

When a note is read, its complete Markdown content is included as a full chat
message. The message includes an **Open in Obsidian** action.

For model-assisted operations, searches send excerpts rather than full vault
content. Targeted edits use the relevant note section or an explicitly selected
note context.

## AI proposal shape

```json
{
  "action": "edit",
  "path": "Projects/Meeting.md",
  "section": "Decisions",
  "content": "- Use SQLite for local persistence",
  "reason": "The user asked to add the decision."
}
```

Supported actions:

- `create`
- `append`
- `edit`
- `replace`
- `delete`
- `open`
- `search`

Model output is parsed as JSON and converted to a typed proposal. Invalid paths,
empty required content, unsupported actions, write-permission failures, and
allowed-folder violations stop execution.

## Review behavior

Generated create, append, edit, and replace proposals are shown in a chat card.
The user can:

- Edit the draft Markdown.
- Preview the draft.
- Confirm the proposal.
- Cancel the proposal.

Existing-note operations capture the note version and send it through `If-Match`.
If the note changes before confirmation, the write fails rather than silently
overwriting newer edits.

Deletion is separate from normal writes:

- It requires `obsidian_allow_delete=true`.
- It requires an exact note path.
- It requires separate confirmation.
- It remains disabled by default in Settings.

## Backend

Primary implementation:

- `backend/app/api/obsidian.py`
- `backend/app/services/obsidian_service.py`
- `backend/app/domain/schemas.py`
- `backend/app/services/settings_service.py`

Primary endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /obsidian/status` | Verify the connection |
| `POST /obsidian/test` | Test unsaved connection fields |
| `POST /obsidian/search` | Search notes directly |
| `GET /obsidian/notes/{path}` | Read complete note Markdown |
| `POST /obsidian/generate-proposal` | Generate a typed model proposal |
| `POST /obsidian/proposals/confirm` | Execute a confirmed proposal |
| `POST /obsidian/proposals/cancel` | Cancel a proposal |
| `POST /obsidian/execute` | Execute approved existing UI operations |

The `/plan` and `/execute` helpers remain for compatibility with the earlier
implementation. The chat-first UI uses `/generate-proposal` and
`/proposals/confirm`.

## Frontend

Primary implementation:

- `frontend/src/components/ChatWindow.jsx`
- `frontend/src/components/ObsidianChatTools.jsx`
- `frontend/src/components/MessageBubble.jsx`
- `frontend/src/components/SettingsPanel.jsx`

The Obsidian tool menu, draft card, target context, and Open in Obsidian action
are all rendered inside chat. The old form modal
`ObsidianActionModal.jsx` is no longer used.

## Settings

Configure the integration under **Settings → Obsidian**:

- API address
- API key
- HTTPS certificate verification
- Optional local CA certificate path
- Allowed write folder
- Vault display name
- Search/read permission
- Create/edit permission
- Delete permission

The API key is stored server-side in BuddyAI SQLite settings and masked when
returned to the frontend. It must not be placed in a chat prompt or
`VITE_`/browser configuration.

The plugin HTTPS CA is normally downloaded from:

```text
https://127.0.0.1:27124/obsidian-local-rest-api.crt
```

## Security constraints

- Relative vault paths only
- Reject absolute paths, drive-style paths, `..`, and null bytes
- Reject `.obsidian` and the configuration folder
- Write paths must remain inside the configured allowed folder
- API key remains backend-only
- Create uses `If-None-Match: *`
- Existing-note writes require `If-Match`
- Delete requires separate permission and confirmation
- The plugin should remain on the local machine unless remote access is
  deliberately and securely configured

## Validation

Backend coverage is in:

- `backend/test_obsidian_service.py`
- `backend/test_api_routes.py`
- `backend/test_app_structure.py`

Run the backend suite:

```bash
cd backend
venv/bin/python -m unittest discover -s . -p 'test_*.py'
```

Build the frontend:

```bash
cd frontend
npm run build
```
