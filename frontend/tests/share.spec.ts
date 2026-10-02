import { test, expect } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';

test.describe('File2QR Advanced Secure Sharing Flow', () => {
  const sharePassword = 'SecretSharePassword';
  
  test.beforeAll(() => {
    // Ensure test file exists
    const testFilePath = path.join(__dirname, 'testfile.txt');
    if (!fs.existsSync(testFilePath)) {
      fs.writeFileSync(testFilePath, 'This is a test file for E2E testing.');
    }
  });

  test('Full E2E Flow', async ({ page }) => {
    test.setTimeout(120000); // 120 seconds

    const testEmail = `test-${Date.now()}-${Math.random().toString(36).substring(7)}@example.com`;
    const testPassword = 'StrongPassword123!';

    // 1. Register
    await page.goto('/register');
    await page.waitForTimeout(3000);
    await page.locator('input[type="email"]').fill(testEmail);
    await page.locator('input[type="password"]').fill(testPassword);
    await page.locator('#firstName').fill('E2E');
    await page.locator('#lastName').fill('Test');
    await page.locator('button[type="submit"]').click();
    
    // Redirects to login on success
    await expect(page).toHaveURL('/login', { timeout: 15000 });
    await page.waitForTimeout(3000);

    // 2. Login
    await page.locator('input[type="email"]').fill(testEmail);
    await page.locator('input[type="password"]').fill(testPassword);
    await page.locator('button[type="submit"]').click();
    
    // Redirects to dashboard
    await expect(page).toHaveURL('/dashboard', { timeout: 15000 });
    
    // 3. Upload File
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.click('text=Click or drag a file to upload');
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles(path.join(__dirname, 'testfile.txt'));
    await page.click('button:has-text("Confirm Upload")');
    
    await expect(page.locator('text=testfile.txt')).toBeVisible({ timeout: 15000 });

    // 4. Create Password Protected Share
    await page.click('button:has-text("Share / QR")'); 
    await expect(page.locator('text=Create Secure Share')).toBeVisible();
    await page.fill('input[type="password"]', sharePassword);
    
    let shareUrl = '';
    page.on('dialog', async dialog => {
      await dialog.accept();
    });
    
    const responsePromise = page.waitForResponse(response => response.url().includes('/api/v1/shares/') && response.request().method() === 'POST');
    await page.click('button:has-text("Create & Copy Link")');
    const response = await responsePromise;
    const data = await response.json();
    shareUrl = data.share_url;
    
    expect(shareUrl).toContain('/f/');
    
    // 5. Open Public Share in new context (unauthenticated)
    const publicContext = await page.context().browser()!.newContext();
    const publicPage = await publicContext.newPage();
    
    await publicPage.goto(shareUrl);
    await expect(publicPage.locator('text=testfile.txt')).toBeVisible();
    await expect(publicPage.locator('text=This file is password protected')).toBeVisible();
    
    // 6. Wrong password rejected
    await publicPage.fill('input[type="password"]', 'wrongpassword');
    await publicPage.click('button:has-text("Unlock Access")');
    await expect(publicPage.locator('text=Incorrect password')).toBeVisible({ timeout: 15000 });
    
    // 7. Correct password accepted
    await publicPage.fill('input[type="password"]', sharePassword);
    await publicPage.click('button:has-text("Unlock Access")');
    await expect(publicPage.locator('text=Download File')).toBeVisible({ timeout: 15000 });
    
    // 8. Download
    const downloadPromise = publicPage.waitForResponse(r => r.url().includes('/download/') && r.request().method() === 'POST');
    await publicPage.click('button:has-text("Download File")');
    const downloadResponse = await downloadPromise;
    expect(downloadResponse.status()).toBe(200);
    
    await publicContext.close();
    
    // 9. Dashboard - Token Regeneration & Revoke
    await page.goto('/dashboard/shares');
    await expect(page.locator('text=Active & Revoked Links')).toBeVisible();
    
    const regenPromise = page.waitForResponse(r => r.url().includes('/regenerate-token/') && r.request().method() === 'POST');
    await page.click('button:has-text("Regen Token")');
    const regenResp = await regenPromise;
    const regenData = await regenResp.json();
    const newShareUrl = regenData.share_url;
    expect(newShareUrl).not.toEqual(shareUrl);
    
    // Verify old token is rejected
    const oldTokenContext = await page.context().browser()!.newContext();
    const oldTokenPage = await oldTokenContext.newPage();
    await oldTokenPage.goto(shareUrl);
    await expect(oldTokenPage.locator('text=Link Unavailable')).toBeVisible();
    await oldTokenContext.close();
    
    // Revoke share
    await page.click('button:has-text("Revoke")');
    await expect(page.locator('text=REVOKED')).toBeVisible();
  });
});
