# Real-Time Notification System API Documentation

## Overview
The system now includes real-time notifications using **WebSocket** connections and **REST API** endpoints for notifications.

---

## 🔌 WebSocket API

### Connection URL
```
ws://localhost:8000/ws/notifications/
```

### Authentication
- Only authenticated users can connect
- The connection automatically joins user-specific notification channels
- Also joins global notifications channel for system-wide announcements

### Message Types Received

#### 1. User-Specific Notification
```json
{
  "type": "notification",
  "notification": {
    "id": 123,
    "title": "New Job Application",
    "message": "Someone applied to your job posting",
    "notification_type": "job_application",
    "is_read": false,
    "link": "/employers/applicants/",
    "created_at": "2026-01-05T10:30:00Z"
  }
}
```

#### 2. Global Notification
```json
{
  "type": "global_notification",
  "notification": {
    "id": 456,
    "title": "System Maintenance",
    "message": "The system will undergo maintenance tonight",
    "level": "warning",
    "created_at": "2026-01-05T10:30:00Z"
  }
}
```

### Message Types Sent

#### Mark Notification as Read
```json
{
  "action": "mark_read",
  "notification_id": 123
}
```

---

## 🌐 REST API Endpoints

### 1. Get User Notifications
**Endpoint:** `GET /api/notifications/`  
**Authentication:** Required  
**Description:** Get all notifications for the authenticated user

**Response:**
```json
{
  "count": 25,
  "unread_count": 5,
  "notifications": [
    {
      "id": 123,
      "title": "New Message",
      "message": "You have a new message from employer",
      "notification_type": "message",
      "is_read": false,
      "link": "/messages/",
      "created_at": "2026-01-05T10:30:00Z"
    }
  ]
}
```

### 2. Mark Notification as Read
**Endpoint:** `POST /api/notifications/<notification_id>/mark-read/`  
**Authentication:** Required  
**Description:** Mark a specific notification as read

**Response:**
```json
{
  "success": true,
  "message": "Notification marked as read"
}
```

### 3. Mark All Notifications as Read
**Endpoint:** `POST /api/notifications/mark-all-read/`  
**Authentication:** Required  
**Description:** Mark all user notifications as read

**Response:**
```json
{
  "success": true,
  "message": "5 notifications marked as read",
  "count": 5
}
```

### 4. Get Global Notifications
**Endpoint:** `GET /api/global-notifications/`  
**Authentication:** Not required  
**Description:** Get all active global notifications (system announcements)

**Response:**
```json
{
  "count": 2,
  "notifications": [
    {
      "id": 456,
      "title": "System Maintenance",
      "message": "The system will undergo maintenance tonight",
      "level": "warning",
      "created_at": "2026-01-05T10:30:00Z",
      "expires_at": "2026-01-06T10:30:00Z"
    }
  ]
}
```

---

## 📡 How It Works

### WebSocket Flow

1. **User logs in** → WebSocket connection established automatically
2. **Admin creates notification** → Signal triggers `broadcast_notification()`
3. **Notification sent** → WebSocket pushes to user's channel
4. **Client receives** → Browser displays toast + updates badge count
5. **Auto-reconnect** → If connection drops, auto-reconnect with exponential backoff

### Notification Types

- `job_application` - New job application
- `job_post` - New job posting
- `message` - New message
- `profile_view` - Profile view
- `post_like` - Post liked
- `connection` - New connection
- `system` - System notification

### Global Notification Levels

- `info` - Blue, informational messages
- `warning` - Yellow, warnings
- `danger` - Red, critical alerts

---

## 🚀 Usage Examples

### JavaScript WebSocket Client
```javascript
const wsUrl = 'ws://localhost:8000/ws/notifications/';
const socket = new WebSocket(wsUrl);

socket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    
    if (data.type === 'notification') {
        console.log('New notification:', data.notification);
        // Update UI, show toast, etc.
    }
};
```

### Fetch API REST Call
```javascript
// Get all notifications
fetch('/api/notifications/', {
    method: 'GET',
    headers: {
        'X-Requested-With': 'XMLHttpRequest'
    }
})
.then(response => response.json())
.then(data => console.log(data));

// Mark notification as read
fetch('/api/notifications/123/mark-read/', {
    method: 'POST',
    headers: {
        'X-CSRFToken': getCookie('csrftoken')
    }
})
.then(response => response.json())
.then(data => console.log(data));
```

---

## 🎯 Features

✅ Real-time push notifications via WebSocket  
✅ Automatic reconnection with exponential backoff  
✅ Browser push notifications (if permission granted)  
✅ Toast notifications for visual feedback  
✅ Separate channels for user-specific and global notifications  
✅ REST API for programmatic access  
✅ Auto-updates notification badges  
✅ Works for both jobseekers and employers  
✅ Signal-based broadcasting (automatic on creation)

---

## 🔧 Technical Details

- **WebSocket Server:** Django Channels with InMemoryChannelLayer
- **Protocol:** WebSocket (ws://) or secure WebSocket (wss://)
- **Connection:** Persistent, bidirectional
- **Reconnection:** Exponential backoff (max 5 attempts)
- **Broadcasting:** Channel groups (`user_{id}_notifications`, `global_notifications`)
- **Signals:** `post_save` on `Notification` and `GlobalNotification` models

---

## 🐛 Troubleshooting

### WebSocket not connecting?
1. Check if Django server is running: `python manage.py runserver`
2. Check browser console for errors
3. Verify `CHANNEL_LAYERS` is configured in settings.py
4. Ensure `channels` is installed: `pip install channels`

### Notifications not appearing?
1. Check if user is authenticated
2. Verify signals are working (check console logs)
3. Inspect browser developer tools → Network → WS tab
4. Check if `show_on_site` and `is_active` are True for global notifications

### API returning 403/404?
1. Ensure user is logged in (for protected endpoints)
2. Verify CSRF token is included in POST requests
3. Check URL patterns match exactly

---

## 📝 Notes

- WebSocket connections automatically establish on page load for authenticated users
- Global notifications are broadcast to ALL connected users
- User notifications are sent only to the specific user's channel
- Browser notifications require user permission
- InMemoryChannelLayer is used (for production, consider Redis)
