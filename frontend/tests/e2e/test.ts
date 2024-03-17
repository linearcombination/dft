import { expect, test } from '@playwright/test'

test('test ui part 1', async ({ page }) => {
    await page.goto('http://localhost:8001/languages')
    await page.getByText('Assamese').click()
    // await page.getByText('Vietnamese').click()
    await page.getByRole('button', { name: 'Next' }).click()
    // await page.getByText('Galatians').click()
    // await page.getByRole('button', { name: 'Next' }).click()
    // await page.getByText('Assamese Unlocked Literal Bible (ulb)').click()
    // await page.getByText('Vietnamese Unlocked Literal Bible (ulb)').click()
    // await page.getByRole('button', { name: 'Next' }).click()
    // await page.getByRole('button', { name: 'Generate File' }).click()
    // const page1Promise = page.waitForEvent('popup')
    // await page.getByRole('button', { name: 'Download Docx' }).click()
    // const page1 = await page1Promise
})
