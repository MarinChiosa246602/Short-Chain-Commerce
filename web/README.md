# Short Chain Commerce - Web Dashboard

React-based dashboard for the logistics data extraction system.

## Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Environment Variables

Create a `.env` file in the web directory:

```
VITE_API_URL=http://localhost:8000
```

## Features

- **Dashboard**: Overview of extraction metrics and recent activity
- **New Extraction**: Upload and process images for logistics data extraction
- **History**: Browse and manage past extractions
- **Settings**: Configure pipeline preferences
- **Dark/Light Theme**: Toggle between themes
- **Responsive Design**: Works on desktop and mobile

## Tech Stack

- React 18
- Vite
- Axios
- Lucide React (icons)
- CSS Variables (theming)
