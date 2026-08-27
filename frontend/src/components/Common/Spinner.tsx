import React from "react";

export const Spinner: React.FC<{ size?: number }> = ({ size = 40 }) => (
  <div
    className="spinner"
    style={{ width: size, height: size, borderTopColor: 'hsl(var(--primary))' }}
    role="status"
    aria-label="loading"
  />
);
