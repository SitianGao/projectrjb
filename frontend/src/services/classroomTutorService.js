import client from '../api/client'

export async function askClassroomTutor(classroomId, sessionId, payload) {
  return client.post(`/classrooms/${classroomId}/sessions/${sessionId}/tutor/chat`, payload)
}

export async function checkTutorIntervention(classroomId, sessionId, payload) {
  return client.post(`/classrooms/${classroomId}/sessions/${sessionId}/tutor/interventions/check`, payload)
}
