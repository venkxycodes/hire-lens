import { test, expect } from "@playwright/test";

test("recruiter workflow from role setup to shortlist and saved outreach", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await page.getByLabel("Username").fill(process.env.E2E_USERNAME || "demo");
  await page
    .getByLabel("Password", { exact: true })
    .fill(process.env.E2E_PASSWORD || "");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Your roles" })).toBeVisible();
  await page.screenshot({
    path: "../docs/screenshots/roles-desktop.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: /Senior Backend Engineer/ }).click();
  await expect(
    page.getByRole("button", { name: "Review Alex Rivera", exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: "../docs/screenshots/candidates-desktop.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Review Alex Rivera", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Match by criterion" }),
  ).toBeVisible();
  await page.screenshot({
    path: "../docs/screenshots/candidate-review.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page.getByRole("button", { name: "All roles", exact: true }).click();
  await page.getByRole("button", { name: "Create role", exact: true }).click();
  const title = `Recruiter E2E ${Date.now()}`;
  await page.getByLabel("Job title").fill(title);
  await page.getByLabel("Department", { exact: true }).fill("Engineering");
  await page.getByLabel("Location", { exact: true }).fill("Remote");
  await page
    .getByRole("textbox", { name: "Job description", exact: true })
    .fill(
      "Build reliable Python Django REST APIs with PostgreSQL, production monitoring and automated testing. Own outcomes and collaborate with product.",
    );
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Create role", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: title, exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Add resumes", exact: true })
    .first()
    .click();
  await page.route("**/resumes/", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 500));
    await route.continue();
  });
  await page.getByLabel("Choose resume files").setInputFiles([
    {
      name: "jordan.txt",
      mimeType: "text/plain",
      buffer: Buffer.from(
        "Jordan Test\njordan@example.com\nBuilt Python Django REST APIs with PostgreSQL testing, production monitoring and deployment. Owned outcomes and collaborated with product.",
      ),
    },
    {
      name: "broken.txt",
      mimeType: "text/plain",
      buffer: Buffer.from("short"),
    },
  ]);
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(page.getByText("failed", { exact: true })).toBeVisible();
  await page.unroute("**/resumes/");
  await expect(page.getByText("added", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Paste resume", exact: true }).click();
  await page.getByLabel("Candidate name", { exact: true }).fill("Alex Test");
  await page.getByLabel("Email (optional)").fill("alex@example.com");
  await page
    .getByLabel("Resume text", { exact: true })
    .fill(
      "Alex Test\nPython Django engineer with production APIs and testing experience. Ownership of outcomes and collaboration with product teams.",
    );
  await page
    .getByRole("button", { name: "Add candidate", exact: true })
    .click();
  await expect(page.getByText("added", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Done", exact: true }).click();
  await page
    .getByRole("button", { name: "Evaluate candidates", exact: true })
    .click();
  await expect(page.locator("tbody .score")).toHaveCount(2, { timeout: 20000 });
  await page
    .getByRole("button", { name: "Review Alex Test", exact: true })
    .click();
  await page.getByRole("button", { name: "Shortlist", exact: true }).click();
  await expect(page.getByLabel("Candidate stage")).toHaveValue("shortlisted");
  await page.getByRole("button", { name: "Notes & activity" }).click();
  await page
    .getByLabel("Recruiter notes")
    .fill("Ask about database migration ownership.");
  page.once("dialog", (dialog) => dialog.dismiss());
  await page.getByRole("button", { name: "Close dialog" }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.getByRole("button", { name: "Save notes", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Save notes", exact: true }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Outreach", exact: true }).click();
  await page
    .getByRole("textbox", { name: "Message", exact: true })
    .fill("Hi Alex, would you be open to discussing our backend role?");
  await page.getByRole("button", { name: "Save draft", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Save draft", exact: true }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page
    .getByRole("button", { name: "Review Alex Test", exact: true })
    .click();
  await page.getByRole("button", { name: "Outreach", exact: true }).click();
  await expect(
    page.getByRole("textbox", { name: "Message", exact: true }),
  ).toHaveValue("Hi Alex, would you be open to discussing our backend role?");
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page.getByRole("button", { name: "Role & criteria" }).click();
  await page
    .getByRole("textbox", { name: "Job description", exact: true })
    .fill(
      "Changed role: Build Python Django APIs and own Kubernetes infrastructure.",
    );
  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(
    page.locator("tbody").getByText("Criteria changed", { exact: true }),
  ).toHaveCount(2);
  await page
    .getByRole("button", { name: "Evaluate candidates", exact: true })
    .click();
  await expect(page.locator("tbody .score")).toHaveCount(2, { timeout: 20000 });
  await page.getByLabel("Filter by stage").selectOption("shortlisted");
  await expect(page.locator("tbody tr")).toHaveCount(1);
  await page.getByLabel("Search candidates").fill("nobody-matches");
  await expect(
    page.getByRole("heading", { name: "No candidates match these filters." }),
  ).toBeVisible();
  await page.getByLabel("Search candidates").fill("");
  await expect(page.locator("tbody tr")).toHaveCount(1);
  await page.getByRole("button", { name: "All roles", exact: true }).click();
  await page.getByRole("button", { name: /Senior Backend Engineer/ }).click();
  await expect(page.locator("tbody tr")).toHaveCount(6);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({
    path: "../docs/screenshots/mobile.png",
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  expect(errors).toEqual([]);
});
