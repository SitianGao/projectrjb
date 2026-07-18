import client from '../api/client'

export async function createClassroomSession(classroomId) {
  return client.post(`/classrooms/${classroomId}/sessions`)
}

export async function updateClassroomScene(classroomId, sessionId, sceneId, payload) {
  return client.patch(`/classrooms/${classroomId}/sessions/${sessionId}/scenes/${sceneId}`, payload)
}

export async function submitClassroomQuiz(classroomId, sessionId, answers) {
  return client.post(`/classrooms/${classroomId}/sessions/${sessionId}/quiz/submit`, { answers })
}

export async function completeClassroom(classroomId, sessionId) {
  return client.post(`/classrooms/${classroomId}/sessions/${sessionId}/complete`)
}
