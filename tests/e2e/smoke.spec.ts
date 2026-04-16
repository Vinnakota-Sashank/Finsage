import { test, expect } from "@playwright/test";

test("landing page renders", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Talk to your money. It finally talks back.")).toBeVisible();
});

test("chat route loads", async ({ page }) => {
  await page.goto("/chat");
  await expect(page.getByText("FinSage AI").first()).toBeVisible();
});

test("forecasting route loads", async ({ page }) => {
  await page.goto("/forecasting");
  await expect(page.getByText("Spending Forecast — Next 3 Months")).toBeVisible();
});

test("simulator route loads", async ({ page }) => {
  await page.goto("/simulator");
  await expect(page.getByText("Probability Distribution (1,000 Simulations)")).toBeVisible();
});

test("alerts route loads", async ({ page }) => {
  await page.goto("/alerts");
  await expect(page.getByText("Proactive Intelligence Alerts")).toBeVisible();
});

test("tax route loads", async ({ page }) => {
  await page.goto("/tax");
  await expect(page.getByText("Section 80C — Tax Saving Tracker (FY 2025-26)")).toBeVisible();
});

test("ingestion route loads", async ({ page }) => {
  await page.goto("/ingestion");
  await expect(page.getByText("Data Ingestion")).toBeVisible();
});
