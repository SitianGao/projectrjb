import client from '../api/client'

export async function evaluateClassroom(classroomId, sessionId) {
  return client.post(`/classrooms/${classroomId}/sessions/${sessionId}/evaluate`)
}
