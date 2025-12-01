# Frontend - Audio Transcription Web App

React + TypeScript frontend for the audio transcription application.

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **ESLint** - Code linting

## Project Structure

```
frontend/
├── src/
│   ├── components/      # React components
│   │   ├── DropZone.tsx
│   │   ├── ProcessingSection.tsx
│   │   ├── OutputSection.tsx
│   │   └── ErrorAlert.tsx
│   ├── hooks/           # Custom React hooks
│   │   └── useTranscription.ts
│   ├── services/         # API services
│   │   └── transcriptionService.ts
│   ├── types/            # TypeScript types
│   │   └── index.ts
│   ├── utils/           # Utility functions
│   │   └── fileUtils.ts
│   ├── config/          # Configuration
│   │   └── api.ts
│   ├── App.tsx          # Main app component
│   ├── main.tsx         # Entry point
│   ├── index.css        # Global styles
│   └── App.css
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## Development

### Install Dependencies

```bash
npm install
```

### Run Development Server

```bash
npm run dev
```

Opens at `http://localhost:8000`

### Build for Production

```bash
npm run build
```

Outputs to `dist/` directory.

### Type Checking

```bash
npm run type-check
```

### Linting

```bash
npm run lint
```

### Testing

```bash
# Run tests
npm run test

# Run tests in watch mode
npm run test

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage
```

## Best Practices Followed

✅ **TypeScript**: Full type safety
✅ **Component-based**: Reusable React components
✅ **Custom Hooks**: Logic separated from UI
✅ **Service Layer**: API calls abstracted
✅ **Error Handling**: Proper error boundaries
✅ **Clean Code**: Single responsibility, DRY principles
✅ **Modern React**: Hooks, functional components
✅ **Build Optimization**: Vite for fast builds
✅ **Testing**: Comprehensive test coverage with Vitest and React Testing Library

## Configuration

Update `src/config/api.ts` to set your backend API URL:

```typescript
export const API_BASE_URL = 'https://your-backend-url.onrender.com';
```

