---
description: AI rules derived by SpecStory from the project AI interaction history
globs: *
---

## <headers/>

## PROJECT DOCUMENTATION & CONTEXT SYSTEM

## TECH STACK

## CODING STANDARDS

## WORKFLOW & RELEASE RULES

## DEBUGGING

When encountering "Failed to fetch" errors in HTML visualizations, suspect CORS issues due to opening files directly in a browser without a local web server. Ensure HTML files are served through a web server to allow JavaScript fetch requests to load data properly. If opening HTML files directly (using the `` protocol), JavaScript fetch requests may fail due to Cross-Origin Resource Sharing (CORS) restrictions. A simple HTTP server can be started to serve the files and resolve this issue.