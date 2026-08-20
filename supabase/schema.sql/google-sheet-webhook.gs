/**
 * Paste this whole file into: your Google Sheet → Extensions → Apps Script
 * (replacing whatever's in Code.gs by default), then deploy it as a Web App.
 * See the setup guide for exact steps.
 *
 * What it does: whenever api/subscribe.py sends a new subscriber, this
 * appends one row: [timestamp, name, email] to the active sheet.
 */
function doPost(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var data = JSON.parse(e.postData.contents);

  sheet.appendRow([
    new Date(),
    data.name || "",
    data.email || ""
  ]);

  return ContentService
    .createTextOutput(JSON.stringify({ status: "ok" }))
    .setMimeType(ContentService.MimeType.JSON);
}