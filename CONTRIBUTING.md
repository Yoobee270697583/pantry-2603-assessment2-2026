# Pantry - Branching & Contribution Guide

## Overview

To keep development organised and reduce merge conflicts, all team members should follow the workflow outlined below.

---

## Branch Structure

### Main Branch

`main`

The main branch should always contain stable and working code.

Do not commit directly to `main` unless making repository-wide administrative changes (e.g. `.gitignore`, documentation updates, or project setup files).

---

## Feature Branches

All development work should be completed in feature branches.

Examples:

```text
feature/authentication
feature/pantry-management
feature/recipe-api
feature/meal-planner
feature/shopping-list
feature/htmx-updates
```

Create a new branch before starting work:

```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

---

## Development Workflow

### 1. Pull Latest Changes

Before starting work:

```bash
git checkout main
git pull origin main
```

### 2. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 3. Complete Work

Make changes related only to the feature assigned.

### 4. Commit Changes

Use clear and descriptive commit messages.

Examples:

```bash
git commit -m "Add user registration functionality"
git commit -m "Create pantry item database model"
git commit -m "Implement shopping list generation"
```

### 5. Push Branch

```bash
git push -u origin feature/your-feature-name
```

### 6. Create Pull Request

Open a Pull Request into `main`.

Another team member should review the changes before merging where possible.

---

## Commit Message Guidelines

Use short, descriptive commit messages.

Good Examples:

```text
Add user registration page
Create pantry item model
Implement meal planner routes
Fix shopping list quantity calculation
Update README setup instructions
```

Avoid:

```text
stuff
update
changes
fixed things
```

---

## Project Standards

- Pull latest changes before starting work.
- Keep commits focused on a single task.
- Test changes before pushing.
- Do not commit `.venv`, databases, or environment files.
- Resolve merge conflicts immediately.

---

## Files Ignored by Git

The following files should never be committed:

```text
__pycache__/
*.pyc
*.pyo
.venv/
.env

*.db
*.sqlite

.DS_Store
Thumbs.db
```

---

## Team Members

### Allan

- Product Owner
- UX Designer
- Frontend Developer

### Ben

- Team Lead
- Frontend & Backend Developer
- Documentation

### Adam

- Frontend & Backend Developer

All team members contribute to development and testing throughout the project.
