/**
 * Telemetry - Client-side telemetry and analytics
 * Integrates with OpenTelemetry and custom event tracking
 */

interface TelemetryEvent {
  name: string;
  properties?: Record<string, unknown>;
  duration?: number;
}

class Telemetry {
  private enabled: boolean;
  private correlationId: string | null = null;

  constructor() {
    this.enabled = process.env.NODE_ENV === 'production';
    this.initCorrelationId();
  }

  private initCorrelationId() {
    // Get or generate correlation ID
    this.correlationId = this.getCorrelationIdFromHeader() || this.generateCorrelationId();
  }

  private getCorrelationIdFromHeader(): string | null {
    // Try to get from response headers (if available)
    return null;
  }

  private generateCorrelationId(): string {
    return crypto.randomUUID();
  }

  getCorrelationId(): string {
    return this.correlationId || this.generateCorrelationId();
  }

  trackEvent(event: TelemetryEvent) {
    if (!this.enabled) return;

    const payload = {
      ...event,
      correlationId: this.correlationId,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      userAgent: navigator.userAgent,
    };

    // Send to backend or analytics service
    this.sendToBackend(payload);
  }

  trackPageView(pageName: string) {
    this.trackEvent({
      name: 'page_view',
      properties: { pageName },
    });
  }

  trackError(error: Error, context?: Record<string, unknown>) {
    this.trackEvent({
      name: 'error',
      properties: {
        message: error.message,
        stack: error.stack,
        ...context,
      },
    });
  }

  trackApiCall(endpoint: string, method: string, duration: number, success: boolean) {
    this.trackEvent({
      name: 'api_call',
      properties: {
        endpoint,
        method,
        success,
      },
      duration,
    });
  }

  trackUserAction(action: string, properties?: Record<string, unknown>) {
    this.trackEvent({
      name: 'user_action',
      properties: {
        action,
        ...properties,
      },
    });
  }

  private async sendToBackend(payload: unknown) {
    try {
      await fetch('/api/telemetry', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Correlation-ID': this.correlationId || '',
        },
        body: JSON.stringify(payload),
        credentials: 'include',
      });
    } catch (error) {
      // Silently fail to not affect user experience
      console.error('Telemetry send failed:', error);
    }
  }
}

// Singleton instance
export const telemetry = new Telemetry();
