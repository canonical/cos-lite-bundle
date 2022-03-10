// To run file:
// npx @flood/element-cli run example.ts --no-headless
// element run prom-query-grafana-dashboards.ts --config prom-query-grafana-dashboards.config.js

import { step, By, Until, TestSettings } from '@flood/element'

export const settings: TestSettings = {
  description: "Simulate N SREs load up a dashboard from scratch at the same time",
  stages: [
    { duration: '2m', target: 5 },
    { duration: '2m', target: 10 },
    { duration: '2m', target: 20 },
    { duration: '5d', target: 20 },
  ],
}

export default () => {
  step('1. Log in', async browser => {
    await browser.visit('${GRAFANA_URL}/dashboards')

    const user = By.nameAttr('user')
    const password = By.nameAttr('password')
    const button = By.visibleText('Log in')

    // const grafana_admin_password_response = await fetch('${COS_URL}:8081/helper/grafana/password');
    // const grafana_admin_password = await grafana_admin_password_response.text()
    
    // const grafana_admin_password = await browser.evaluate(async () => { const data = await (await fetch('http://pd-ssd-4cpu-16gb.us-central1-a.c.lma-light-load-testing.internal:8081/helper/grafana/password')).json(); return data })

    await browser.wait(Until.elementIsVisible(user))
    await browser.wait(Until.elementIsVisible(password))
    await browser.wait(Until.elementIsVisible(button))

    await browser.type(user, 'admin')
    await browser.type(password, 'GRAFANA_ADMIN_PASSWORD_TO_SUBSTITUTE_BY_CLOUD_INIT')
    await browser.click(button)
  })

  step('2. Open dashboard', async browser => {
    let dashboard = By.visibleText('sre mock 6 panels - rates')
    await browser.wait(Until.elementIsVisible(dashboard))
    await browser.click(dashboard)
  })

  step('3. Look at dashboard', async browser => {
    // await browser.wait(2 * ${REFRESH_INTERVAL})
    const entire_dashboard_reload_period = 5 * 60  // 5 minutes [sec]
    const min_delay_to_encounter_a_refresh = 2 * ${REFRESH_INTERVAL}  // [sec]
    const time_to_sleep = Math.max(min_delay_to_encounter_a_refresh, entire_dashboard_reload_period - min_delay_to_encounter_a_refresh)  // [sec]

    await new Promise(f => setTimeout(f, time_to_sleep * 1000));
  })
}
