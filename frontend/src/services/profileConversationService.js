import client from '../api/client'

export async function sendCourseProfileMessage(courseId, conversationId, payload) {
  return client.post(`/courses/${courseId}/profile/conversations/${conversationId}/messages`, payload)
}
