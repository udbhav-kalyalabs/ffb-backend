# 📚 FFB Documentation Index

**Purpose:** Central hub for all project documentation  
**Keep:** Only essential reference - detailed docs in subfolders

---

## 🚀 START HERE

**New to this project?**
1. Read: `docs/ROADMAP.md` (4-week plan overview)
2. Read: `docs/session-logs/SESSION_STATUS.md` (current state)
3. Go to: `docs/phase1/` (current phase)

---

## 📁 Folder Structure

```
docs/
├── ROADMAP.md                    ← 4-week implementation plan
├── phase1/                       ← Phase 1: Data annotation & training
│   ├── setup/
│   │   ├── label-studio-setup.md
│   │   ├── gcp-training-setup.md
│   │   └── scripts/
│   │       ├── setup_label_studio.sh
│   │       └── setup_label_studio.bat
│   ├── implementation.md         ← Detailed step-by-step guide
│   ├── checklist.md              ← Progress tracking
│   ├── progress.md               ← Session notes & daily log
│   └── quickstart.md             ← Quick reference
├── architecture/                 ← Technical deep-dives
│   ├── triangulation-algorithm.md
│   └── [future: other components]
├── reference/                    ← Static reference data
│   ├── ground-truth.json         ← Validation data
│   └── implementation-status.md
└── session-logs/                 ← Session continuity
    └── SESSION_STATUS.md         ← Current session state
```

---

## 🎯 Quick Navigation

### By Task
- **Setting up annotation tool:** `docs/phase1/setup/label-studio-setup.md`
- **GCP training setup:** `docs/phase1/setup/gcp-training-setup.md`
- **Ground truth data:** `docs/reference/ground-truth.json`
- **Current progress:** `docs/session-logs/SESSION_STATUS.md`

### By Phase
- **Phase 1:** `docs/phase1/`
- **Architecture:** `docs/architecture/`
- **Reference:** `docs/reference/`

---

## 📊 Current Status
See: `docs/session-logs/SESSION_STATUS.md`

---

**Last Updated:** 2026-04-18
