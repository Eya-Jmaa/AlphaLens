import React from "react";

type State = { hasError: boolean };

export class ErrorBoundary extends React.Component<{ children?: React.ReactNode }, State> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: any, info: any) {
    console.error("ErrorBoundary caught", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 bg-red-50 border border-red-200 rounded">
          <h3 className="font-semibold">Something went wrong</h3>
          <p className="text-sm text-muted-foreground">An unexpected error occurred. Try refreshing the page.</p>
        </div>
      );
    }
    return this.props.children ?? null;
  }
}
