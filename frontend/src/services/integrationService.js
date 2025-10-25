/**
 * Mock Integration Service Layer
 * 
 * This service provides mock implementations for third-party integrations.
 * Replace these with real API calls when API keys are available.
 * 
 * Supported integrations:
 * - Email: Gmail, Mailchimp, AWS SES
 * - SMS: Twilio, AWS SNS
 * - Push Notifications: Firebase
 * - Messaging: WhatsApp Business API, Slack, Discord
 * - Calendar: Google Calendar, Outlook
 */

// ==================== EMAIL SERVICES ====================

export const emailService = {
  /**
   * Send email via Gmail API (MOCKED)
   */
  sendGmail: async ({ to, subject, body, cc = [], bcc = [] }) => {
    console.log('[MOCK] Gmail Send:', { to, subject });
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return {
      success: true,
      provider: 'gmail',
      messageId: `gmail-${Date.now()}`,
      status: 'sent_mock'
    };
  },

  /**
   * Send email via Mailchimp API (MOCKED)
   */
  sendMailchimp: async ({ to, subject, body, templateId = null }) => {
    console.log('[MOCK] Mailchimp Send:', { to, subject, templateId });
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return {
      success: true,
      provider: 'mailchimp',
      campaignId: `mc-${Date.now()}`,
      status: 'sent_mock'
    };
  },

  /**
   * Send email via AWS SES (MOCKED)
   */
  sendSES: async ({ to, subject, body, from }) => {
    console.log('[MOCK] AWS SES Send:', { to, subject, from });
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return {
      success: true,
      provider: 'aws_ses',
      messageId: `ses-${Date.now()}`,
      status: 'sent_mock'
    };
  }
};

// ==================== SMS SERVICES ====================

export const smsService = {
  /**
   * Send SMS via Twilio (MOCKED)
   */
  sendTwilio: async ({ to, message, from = null }) => {
    console.log('[MOCK] Twilio SMS:', { to, message });
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return {
      success: true,
      provider: 'twilio',
      sid: `SM${Date.now()}`,
      status: 'sent_mock'
    };
  },

  /**
   * Send SMS via AWS SNS (MOCKED)
   */
  sendSNS: async ({ to, message }) => {
    console.log('[MOCK] AWS SNS SMS:', { to, message });
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return {
      success: true,
      provider: 'aws_sns',
      messageId: `sns-${Date.now()}`,
      status: 'sent_mock'
    };
  }
};

// ==================== PUSH NOTIFICATION SERVICES ====================

export const pushService = {
  /**
   * Send push notification via Firebase Cloud Messaging (MOCKED)
   */
  sendFirebasePush: async ({ tokens, title, body, data = {} }) => {
    console.log('[MOCK] Firebase Push:', { tokens, title, body });
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return {
      success: true,
      provider: 'firebase',
      messageId: `fcm-${Date.now()}`,
      sentCount: Array.isArray(tokens) ? tokens.length : 1,
      status: 'sent_mock'
    };
  }
};

// ==================== MESSAGING SERVICES ====================

export const messagingService = {
  /**
   * Send WhatsApp message via WhatsApp Business API (MOCKED)
   */
  sendWhatsApp: async ({ to, message, mediaUrl = null }) => {
    console.log('[MOCK] WhatsApp Message:', { to, message, mediaUrl });
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return {
      success: true,
      provider: 'whatsapp',
      messageId: `wa-${Date.now()}`,
      status: 'sent_mock'
    };
  },

  /**
   * Send Slack notification (MOCKED)
   */
  sendSlack: async ({ channel, message, attachments = [] }) => {
    console.log('[MOCK] Slack Message:', { channel, message });
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return {
      success: true,
      provider: 'slack',
      timestamp: Date.now(),
      status: 'sent_mock'
    };
  },

  /**
   * Send Discord notification (MOCKED)
   */
  sendDiscord: async ({ webhookUrl, message, embeds = [] }) => {
    console.log('[MOCK] Discord Webhook:', { message });
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return {
      success: true,
      provider: 'discord',
      messageId: `discord-${Date.now()}`,
      status: 'sent_mock'
    };
  }
};

// ==================== CALENDAR SERVICES ====================

export const calendarService = {
  /**
   * Create Google Calendar event (MOCKED)
   */
  createGoogleCalendarEvent: async ({ summary, description, startTime, endTime, attendees = [] }) => {
    console.log('[MOCK] Google Calendar Event:', { summary, startTime, endTime });
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return {
      success: true,
      provider: 'google_calendar',
      eventId: `gcal-${Date.now()}`,
      link: `https://calendar.google.com/event?eid=mock-${Date.now()}`,
      status: 'created_mock'
    };
  },

  /**
   * Create Outlook Calendar event (MOCKED)
   */
  createOutlookEvent: async ({ subject, body, startTime, endTime, attendees = [] }) => {
    console.log('[MOCK] Outlook Calendar Event:', { subject, startTime, endTime });
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return {
      success: true,
      provider: 'outlook',
      eventId: `outlook-${Date.now()}`,
      link: `https://outlook.office.com/calendar/item/mock-${Date.now()}`,
      status: 'created_mock'
    };
  }
};

// ==================== UNIFIED SEND FUNCTION ====================

/**
 * Send notification via specified provider
 * This is a convenience function that routes to the appropriate service
 */
export const sendNotification = async (provider, type, payload) => {
  try {
    switch (provider.toLowerCase()) {
      // Email
      case 'gmail':
        return await emailService.sendGmail(payload);
      case 'mailchimp':
        return await emailService.sendMailchimp(payload);
      case 'aws_ses':
      case 'ses':
        return await emailService.sendSES(payload);
      
      // SMS
      case 'twilio':
        return await smsService.sendTwilio(payload);
      case 'aws_sns':
      case 'sns':
        return await smsService.sendSNS(payload);
      
      // Push
      case 'firebase':
      case 'fcm':
        return await pushService.sendFirebasePush(payload);
      
      // Messaging
      case 'whatsapp':
        return await messagingService.sendWhatsApp(payload);
      case 'slack':
        return await messagingService.sendSlack(payload);
      case 'discord':
        return await messagingService.sendDiscord(payload);
      
      // Calendar
      case 'google_calendar':
        return await calendarService.createGoogleCalendarEvent(payload);
      case 'outlook':
        return await calendarService.createOutlookEvent(payload);
      
      default:
        throw new Error(`Unknown provider: ${provider}`);
    }
  } catch (error) {
    console.error(`[ERROR] Integration Service (${provider}):`, error);
    return {
      success: false,
      provider,
      error: error.message,
      status: 'failed'
    };
  }
};

// ==================== CONFIGURATION ====================

/**
 * Check if a provider is configured (has API keys)
 * In production, this would check environment variables or database settings
 */
export const isProviderConfigured = (provider) => {
  // For now, all providers return false (mock mode)
  // When real API keys are added, check here
  return false;
};

/**
 * Get available providers for a given type
 */
export const getAvailableProviders = (type) => {
  const providers = {
    email: ['gmail', 'mailchimp', 'aws_ses'],
    sms: ['twilio', 'aws_sns'],
    push: ['firebase'],
    messaging: ['whatsapp', 'slack', 'discord'],
    calendar: ['google_calendar', 'outlook']
  };
  
  return providers[type] || [];
};

export default {
  email: emailService,
  sms: smsService,
  push: pushService,
  messaging: messagingService,
  calendar: calendarService,
  sendNotification,
  isProviderConfigured,
  getAvailableProviders
};
