import { test, expect, Page } from '@playwright/test';

async function mockApi(page: Page) {
  await page.route('http://localhost:8000/**', async (route) => {
    const request = route.request();
    const url = new URL(request.url());

    if (url.pathname === '/health') return route.fulfill({ json: { status: 'ok', ollama_running: true } });
    if (url.pathname === '/conversations') {
      if (request.method() === 'POST') {
        return route.fulfill({ json: { conversation: { id: 2, title: 'New Chat', created_at: new Date().toISOString(), updated_at: new Date().toISOString(), messages: [] } } });
      }
      return route.fulfill({ json: { conversations: [{ id: 1, title: 'Test chat', created_at: new Date().toISOString(), updated_at: new Date().toISOString(), messages: [] }] } });
    }
    if (url.pathname === '/models') return route.fulfill({ json: { models: [{ name: 'qwen2.5-coder:7b', size: 1024 }] } });
    if (url.pathname === '/models/catalog') return route.fulfill({ json: { catalog: [{ name: 'llama3.2', size: 1024 }] } });
    if (url.pathname === '/settings') return route.fulfill({ json: { enable_thinking: false, reasoning_budget: 8192 } });
    if (url.pathname === '/documents') return route.fulfill({ json: { documents: [] } });
    if (url.pathname === '/memories/graph') return route.fulfill({ json: { nodes: [], edges: [] } });
    if (url.pathname.startsWith('/conversations/')) return route.fulfill({ json: { conversation: { id: 1, title: 'Test chat', created_at: new Date().toISOString(), updated_at: new Date().toISOString(), messages: [] } } });

    return route.fulfill({ status: 404, json: { detail: 'Not mocked' } });
  });
}

test.describe('LocalGPT interface', () => {
  test('loads chat workspace and navigation', async ({ page }) => {
    await mockApi(page);
    await page.goto('/');

    await expect(page.getByText('Buddyai', { exact: true }).first()).toBeVisible();
    await expect(page.getByText('Ollama connected')).toBeVisible();
    await expect(page.getByRole('navigation').getByRole('button', { name: 'Knowledge', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Memory Graph' })).toBeVisible();
    await expect(page.getByText('Debug code', { exact: true })).toHaveCount(0);
    await expect(page.getByText('Buddyai', { exact: true })).toBeVisible();
  });

  test('navigates to knowledge, models, memory, and settings', async ({ page }) => {
    await mockApi(page);
    await page.goto('/');

    await page.getByRole('navigation').getByRole('button', { name: 'Knowledge', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Knowledge' })).toBeVisible();

    await page.getByRole('button', { name: 'Models' }).click();
    await expect(page.getByRole('heading', { name: 'Models' })).toBeVisible();

    await page.getByRole('button', { name: 'Memory Graph' }).click();
    await expect(page.getByRole('heading', { name: 'Your Memory Graph is Empty' })).toBeVisible();

    await page.getByRole('button', { name: 'Settings' }).click();
    await expect(page.getByRole('heading', { name: 'Settings', exact: true })).toBeVisible();
  });

  test('new chat and existing chat open the chat tab', async ({ page }) => {
    await mockApi(page);
    await page.goto('/');

    await page.getByRole('button', { name: 'Models', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Models', exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'New chat', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'How can I help?', exact: true })).toBeVisible();

    await page.getByRole('button', { name: 'Models', exact: true }).click();
    await page.getByRole('button', { name: 'Test chat' }).click();
    await expect(page.getByRole('heading', { name: 'Test chat', exact: true })).toBeVisible();
  });

  test('sidebar can collapse and expand', async ({ page }) => {
    await mockApi(page);
    await page.goto('/');

    await page.getByTitle('Collapse sidebar').click();
    await expect(page.getByTitle('Expand sidebar')).toBeVisible();
    await page.getByTitle('Expand sidebar').click();
    await expect(page.getByText('Buddyai', { exact: true })).toBeVisible();
  });

  test('sends a chat prompt to the backend', async ({ page }) => {
    await mockApi(page);
    await page.route('**/chat', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: 'data: {"type":"metadata","model":"qwen2.5-coder:7b","conversation_id":1,"rag_used":false,"sources":[],"memories_used":[],"thinking_enabled":false}\n\ndata: {"type":"content","content":"Hello from LocalGPT"}\n\ndata: {"type":"done"}\n\n',
      });
    });
    await page.goto('/');

    await expect(page.getByRole('button', { name: 'qwen2.5-coder:7b' })).toBeVisible();
    await page.locator('textarea').first().fill('Hello');
    const sendButton = page.getByRole('button', { name: 'Send', exact: true });
    await expect(sendButton).toBeEnabled();
    const chatRequest = page.waitForRequest((request) => request.url().endsWith('/chat') && request.method() === 'POST');
    await sendButton.click();

    const request = await chatRequest;
    expect(request.postDataJSON().prompt).toBe('Hello');
  });
});
