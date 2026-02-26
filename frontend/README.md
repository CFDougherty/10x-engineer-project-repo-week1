# PromptLab Frontend

A React-based frontend for the PromptLab application, built with Vite and TypeScript.

## Features

- **Prompt Management**: Create, read, update, and delete prompts
- **Collections**: Organize prompts into collections
- **Responsive Design**: Works on mobile, tablet, and desktop devices
- **Loading States**: Visual feedback during API operations
- **Error Handling**: User-friendly error messages

## Technologies

- **Framework**: React 18
- **Build Tool**: Vite
- **UI Library**: Material-UI
- **Routing**: React Router DOM
- **HTTP Client**: Axios
- **TypeScript**: Type safety throughout the application

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open your browser to `http://localhost:5173`

## Available Scripts

- `npm run dev`: Start development server
- `npm run build`: Build for production
- `npm run preview`: Preview production build
- `npm run lint`: Run linter
- `npm run type-check`: Run TypeScript type checking

## Project Structure

```
src/
├── components/    # Reusable UI components
├── pages/         # Page-level components
├── hooks/         # Custom React hooks
├── services/      # API service layer
├── types/         # TypeScript type definitions
├── utils/         # Utility functions
├── App.tsx        # Main application component
└── main.tsx       # Application entry point
```

## API Integration

The frontend connects to the PromptLab backend API at `http://localhost:8000` by default. You can configure a different API base URL using the `VITE_API_BASE_URL` environment variable.

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

MIT