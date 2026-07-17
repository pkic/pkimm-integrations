---
date: 2026-07-16T00:00:00Z
title: Eramba
weight: 1
---

# Eramba integration

[Eramba](https://www.eramba.org/) is an open-source GRC platform. This integration packages
the PKI Maturity Model as an Eramba-importable CSV so you can track PKI maturity requirements
as controls in Eramba.

Each CSV row is a requirement (`Item`), grouped by category (`Chapter`), with the assessment
guidance and references in the item's additional information. The package is generated from
the canonical model; do not edit the CSV by hand.

## Download

| Model version | Package |
|---|---|
| 2.0.0 | [`pkimm-2.0.0.csv`](./pkimm-2.0.0.csv) |
| 1.0.0 | [`pkimm-1.0.0.csv`](./pkimm-1.0.0.csv) |

## Importing

1. In Eramba, open the CSV import for the target module.
2. Map the columns in order: Chapter ID, Chapter Name, Chapter Description, Item ID,
   Item Name, Item Description, Item Additional Information (the file has no header row).
3. Complete the import and review the created chapters/items.
