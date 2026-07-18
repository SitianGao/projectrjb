import client from '../api/client'

export async function getDemoClassroom(courseId) {
  return client.get('/classrooms/demo', { params: { course_id: courseId } })
}

export async function getClassroom(classroomId) {
  return client.get(`/classrooms/${classroomId}`)
}

export async function generateClassroom(payload) {
  return client.post('/classrooms/generate', payload)
}

export async function getJob(jobId) {
  return client.get(`/task/${jobId}/status`)
}
