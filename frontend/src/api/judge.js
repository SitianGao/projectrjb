import client from './client'

export async function submitCode({ student_id, problem_id, language, code, resource_id }) {
  const res = await client.post('/judge/submit', {
    student_id,
    problem_id,
    language,
    code,
    resource_id,
  })
  return res
}

export async function getProblems(params = {}) {
  const res = await client.get('/judge/problems', { params })
  return res
}

export async function getProblemDetail(problemId) {
  const res = await client.get(`/judge/problems/${problemId}`)
  return res
}

export async function getLanguages() {
  const res = await client.get('/judge/languages')
  return res
}
