import client from '../api/client'

export async function getCourseProfile(courseId) {
  return client.get(`/courses/${courseId}/profile`)
}

export async function getCourseProfileConversationState(courseId, conversationId) {
  return client.get(`/courses/${courseId}/profile/conversations/${conversationId}/state`)
}

export async function getCurrentCourseProfileConversation(courseId) {
  return client.get(`/courses/${courseId}/profile/conversations/current`)
}

export async function updateCourseProfile(courseId, profilePatch) {
  return client.put(`/courses/${courseId}/profile`, { profile_patch: profilePatch })
}
