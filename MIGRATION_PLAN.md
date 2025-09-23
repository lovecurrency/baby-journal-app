# Baby Journal App - Frontend Migration Plan
## Flask to Next.js + shadcn/ui with MCP

### Project Status
- **Current**: Flask app deployed on Render with templates
- **Target**: Next.js frontend with shadcn/ui components via MCP
- **Strategy**: Dual deployment (Flask API on Render, Next.js on Vercel)

### Architecture Overview
- **Backend**: Flask API on Render (unchanged initially, add CORS)
- **Frontend**: Next.js with shadcn/ui on Vercel/Netlify
- **UI Components**: shadcn/ui via MCP (no custom design)
- **Database**: Supabase PostgreSQL (existing)

## Phase 1: Setup Next.js with shadcn/ui MCP

### 1.1 Create Next.js Project
```bash
npx create-next-app@latest baby-journal-nextjs --typescript --tailwind --app
cd baby-journal-nextjs
```

### 1.2 Initialize shadcn/ui
```bash
npx shadcn@latest init
```

### 1.3 Configure MCP Server
```bash
pnpm dlx shadcn@latest mcp init --client claude
```

### 1.4 Restart Claude Code
- Restart to activate MCP connection
- Verify MCP is working with `/mcp` command

## Phase 2: Flask API Preparation

### 2.1 Add CORS Support
Add to `main_db.py`:
```python
from flask_cors import CORS
CORS(app, origins=['http://localhost:3000', 'https://your-domain.vercel.app'])
```

### 2.2 Required API Endpoints
**Already Available:**
- `/api/activity` (POST) - Add activity
- `/api/statistics` (GET) - Get stats
- `/api/activity/<id>` (PUT/DELETE) - Update/delete activity

**Need to Add:**
- `/api/profile` (GET/POST) - Baby profile
- `/api/activities` (GET) - List all activities
- `/api/upload` (POST) - WhatsApp upload
- `/api/analytics-data` (GET) - Chart data

### 2.3 Deploy to Render
- Commit CORS changes
- Push to GitHub
- Deploy to Render

## Phase 3: Frontend Pages with shadcn/ui Components

### Page Component Mapping

#### 1. Home Dashboard (`app/page.tsx`)
**shadcn/ui components needed:**
- `Card` - Statistics cards
- `Table` - Recent activities
- `Button` - Navigation/actions
- `Badge` - Activity types
- `Avatar` - Baby profile display

#### 2. Setup Page (`app/setup/page.tsx`)
**shadcn/ui components needed:**
- `Form` - Profile form
- `Input` - Name field
- `Calendar/DatePicker` - Birth date
- `Select` - Gender selection
- `Button` - Submit
- `Label` - Form labels

#### 3. Activities Page (`app/activities/page.tsx`)
**shadcn/ui components needed:**
- `DataTable` - Full activity list
- `DropdownMenu` - Row actions
- `Dialog` - Delete confirmation
- `ScrollArea` - Scrollable list
- `Input` - Search/filter
- `Button` - Actions

#### 4. Quick Add (`app/quick-add/page.tsx`)
**shadcn/ui components needed:**
- `Form` - Activity form
- `Select` - Activity type
- `Textarea` - Notes
- `Button` - Submit
- `Toast` - Success notification
- `RadioGroup` - Quick options

#### 5. Upload Page (`app/upload/page.tsx`)
**shadcn/ui components needed:**
- `Card` - Upload container
- `Input` (type="file") - File selection
- `Progress` - Upload progress
- `Alert` - Status/errors
- `Button` - Upload trigger

#### 6. Analytics (`app/analytics/page.tsx`)
**shadcn/ui components needed:**
- `Tabs` - Chart categories
- `Card` - Chart containers
- `Select` - Date range
- `Skeleton` - Loading states
- `Table` - Data tables
- External: Chart.js or Recharts for graphs

### Layout Components (`app/layout.tsx`)
**shadcn/ui components needed:**
- `NavigationMenu` - Top navigation
- `Sheet` - Mobile menu
- `Button` - Menu triggers
- `Separator` - Visual dividers
- `ThemeToggle` - Dark/light mode

## Phase 4: API Integration Layer

### 4.1 Create API Client (`lib/api.ts`)
```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://baby-journal.onrender.com';

export const api = {
  // Profile
  getProfile: () => fetch(`${API_URL}/api/profile`),
  createProfile: (data) => fetch(`${API_URL}/api/profile`, {method: 'POST', ...}),

  // Activities
  getActivities: () => fetch(`${API_URL}/api/activities`),
  addActivity: (data) => fetch(`${API_URL}/api/activity`, {method: 'POST', ...}),
  updateActivity: (id, data) => fetch(`${API_URL}/api/activity/${id}`, {method: 'PUT', ...}),
  deleteActivity: (id) => fetch(`${API_URL}/api/activity/${id}`, {method: 'DELETE'}),

  // Analytics
  getStatistics: () => fetch(`${API_URL}/api/statistics`),
  getAnalyticsData: () => fetch(`${API_URL}/api/analytics-data`),

  // Upload
  uploadWhatsApp: (file) => fetch(`${API_URL}/api/upload`, {method: 'POST', ...})
};
```

### 4.2 Environment Configuration
```env
# .env.local
NEXT_PUBLIC_API_URL=https://baby-journal.onrender.com
```

## Phase 5: Development Workflow

### 5.1 MCP Component Addition Workflow
1. Use MCP to browse shadcn registry: `"Show me Card components from shadcn"`
2. Add components: `"Add the Card component"`
3. Use components in pages
4. Let MCP handle imports and setup

### 5.2 Testing Locally
```bash
# Terminal 1: Next.js
npm run dev

# Browser: http://localhost:3000
# API calls go to production Render backend
```

## Phase 6: Deployment

### 6.1 Deploy to Vercel
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set environment variables in Vercel dashboard
NEXT_PUBLIC_API_URL=https://baby-journal.onrender.com
```

### 6.2 Update Flask CORS
Update `main_db.py` with Vercel domain:
```python
CORS(app, origins=[
    'http://localhost:3000',
    'https://baby-journal.vercel.app'  # Your Vercel domain
])
```

## Project Structure
```
/Users/priyanktiwari/Desktop/Coding/
├── baby-journal-app/          # Current Flask app (stays on Render)
│   ├── main_db.py            # Add CORS and JSON endpoints
│   ├── templates/            # Keep for now (fallback)
│   └── MIGRATION_PLAN.md     # This file
│
└── baby-journal-nextjs/       # New Next.js frontend
    ├── app/
    │   ├── layout.tsx        # Main layout with navigation
    │   ├── page.tsx          # Home dashboard
    │   ├── setup/
    │   │   └── page.tsx      # Baby profile setup
    │   ├── activities/
    │   │   └── page.tsx      # Activities list
    │   ├── quick-add/
    │   │   └── page.tsx      # Quick add form
    │   ├── upload/
    │   │   └── page.tsx      # WhatsApp upload
    │   └── analytics/
    │       └── page.tsx      # Analytics dashboard
    ├── components/
    │   └── ui/               # shadcn/ui components (via MCP)
    ├── lib/
    │   └── api.ts           # Flask API client
    └── components.json       # shadcn configuration

```

## Migration Checklist

### Pre-Migration
- [ ] Backup current database
- [ ] Document Render app URL
- [ ] List any custom styles to preserve

### Phase 1: Setup
- [ ] Create Next.js project
- [ ] Initialize shadcn/ui
- [ ] Setup MCP server
- [ ] Restart Claude Code with MCP

### Phase 2: Backend
- [ ] Add CORS to Flask
- [ ] Create missing JSON endpoints
- [ ] Deploy to Render
- [ ] Test CORS with curl/Postman

### Phase 3: Frontend Development
- [ ] Setup page with shadcn Form components
- [ ] Home dashboard with Cards and Tables
- [ ] Activities page with DataTable
- [ ] Quick Add with Form and Toast
- [ ] Upload page with file handling
- [ ] Analytics with Charts

### Phase 4: Integration
- [ ] Create API client library
- [ ] Add error handling
- [ ] Implement loading states
- [ ] Add authentication if needed

### Phase 5: Testing
- [ ] Test all CRUD operations
- [ ] Verify file uploads work
- [ ] Check analytics data display
- [ ] Mobile responsiveness

### Phase 6: Deployment
- [ ] Deploy to Vercel
- [ ] Configure environment variables
- [ ] Update Flask CORS with production URL
- [ ] DNS configuration if using custom domain

### Post-Migration
- [ ] Monitor for errors
- [ ] Gather user feedback
- [ ] Plan deprecation of Flask templates
- [ ] Document API for future reference

## Important Notes

1. **Zero Downtime**: Flask app remains live throughout migration
2. **MCP Usage**: Use MCP for ALL component additions - no custom components
3. **API First**: Ensure Flask API is ready before building frontend features
4. **Testing**: Test each feature locally before deployment
5. **Rollback Plan**: Keep Flask templates functional as fallback

## Commands Reference

```bash
# Next.js Development
npm run dev          # Start dev server
npm run build       # Build for production
npm run lint        # Run linter

# shadcn/ui via MCP (in Claude)
"Show me Button components from shadcn"
"Add the Button component"
"Show me Form examples from shadcn"

# Deployment
vercel              # Deploy to Vercel
vercel --prod       # Deploy to production

# Flask (on Render)
git push            # Auto-deploys to Render
```

## Render App Details
- **Current URL**: [To be filled in by user]
- **API Base**: [To be filled in by user]
- **Deploy Hook**: [To be filled in by user]

---

Last Updated: 2025-09-23
Status: Planning Phase - Ready to Execute