import client from './client'

/**
 * 运行交互式代码实验
 */
export async function runExperiment({ code, student_id, experiment_id, parameters, time_limit_sec }) {
  const res = await client.post('/judge/experiment', {
    code,
    student_id,
    experiment_id,
    parameters,
    time_limit_sec,
  })
  return res
}
