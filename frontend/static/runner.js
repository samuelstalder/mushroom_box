async function getData(url) {
  const res = await fetch(url, {
    method: "GET"
  })
  if (res.status != 200) {
    alert("unable to get data from backend")
    return {}
  }
  return await res.json()
}

function buildBody({
  title,
  headers,
  inner
}, append, data) {
  if (data.length == 0) {
    return
  }
  let title_elem = document.createElement("h1")
  title_elem.innerText = title
  const title_elem_id = "head-" + inner
  title_elem.id = title_elem_id
  title_elem.style.textAlign = "center"
  // draw the body
  let table = document.createElement("table")
  const table_id = "data-" + inner
  table.id = table_id
  if (append) {
    table.classList.add("mx-auto")
    table.classList.add("hideable-tables")
    table.classList.add("hidden")
  } else {
    const org = document.getElementById(table_id)
    table.classList = org.classList
  }
  // add external header
  let tr = document.createElement("tr")
  for (const element of headers.external) {
    let th = document.createElement("th")
    th.innerText = element
    tr.append(th)
  }
  table.appendChild(tr)
  // render data
  let mapping = data["mapping"]
  for (const row of data["values"]) {
    let tr = document.createElement("tr")
    for (const element of headers.internal) {
      let th = document.createElement("th")
      th.innerText = row[mapping[element]]
      tr.append(th)
    }
    table.appendChild(tr)
  }
  if (append) {
    // new data block
    document.body.appendChild(title_elem)
    document.body.appendChild(table)
  } else {
    for (let [id, elem] of [
        [table_id, table],
        // [title_elem_id, title_elem]
      ]) {
      const old = document.getElementById(id)
      document.body.replaceChild(elem, old)
    }
  }
}

function newChartContainer(id) {
  // <div id="chartContainer" style="height: 300px; width: 100%;"></div>
  let container = document.createElement("div")
  container.id = id
  container.style.height = "300px"
  container.style.width = "100%"
  return container
}

function newChart(name, title, count) {
  let data = []
  for (let i = 0; i < count; i += 1) {
    data.push({
      type: "area",
      dataPoints: []
    })
  }

  return new CanvasJS.Chart(name, {
    // theme: "light2", // "light1", "light2", "dark1", "dark2"
    animationEnabled: true,
    zoomEnabled: true,
    title: {
      text: title
    },
    toolTip: {
      shared: true
    },
    axisX: {
      title: "Timeline",
      gridThickness: 2
    },
    axisY: {
      title: "Celcius °"
    },
    data: data
  })
}

function setCalendarDate() {
  let dates = []
  const params = new URLSearchParams(window.location.search)

  for (let entry of ["since", "until"]) {
    let ival = params.get(entry)
    if (ival === null) {
      break
    }
    // JS does not use unix datetime
    dates.push(new Date(parseInt(ival) * 1000))
  }

  return dates
}

function setupCalendar(id, onclose) {
  let options = {
    enableTime: true,
    dateFormat: "Y-m-d H:i",
    maxDate: "today",
    mode: "range",
    time_24hr: true,
    onClose: onclose
  }

  let idates = setCalendarDate()
  if (idates.length > 0) {
    options["defaultDate"] = idates
  }

  return flatpickr("#" + id, options)
}
class Runner {
  constructor(bodies, endID, calendarID) {
    this.has_run = false
    this.endID = endID
    this.interval_id = undefined
    this.charts = []
    this.bodies = bodies
    this.calendarID = calendarID
    this.calendar = undefined
  }
  async run() {
    const bodies = this.bodies
    let resultingData = []
    for (let i = 0; i < bodies.length; i += 1) {
      let res = getData(bodies[i].url)
      resultingData.push(res)
    }
    resultingData = await Promise.all(resultingData)

    // create datepicker
    if (!this.has_run) {
      this.calendar = setupCalendar(this.calendarID, (selectedDates, _dateStr, _instance) => {
        const url = new URL(window.location.href)
        if (selectedDates.length == 0) {
          return
        }

        // only since
        const since = selectedDates[0].getTime() / 1000 // JS gives milliseconds unix time is in seconds
        url.searchParams.delete("since")
        url.searchParams.delete("until")
        url.searchParams.append("since", since)

        // both since and until
        if (selectedDates.length > 1) {
          const until = selectedDates[selectedDates.length - 1].getTime() / 1000 // JS gives milliseconds unix time is in seconds
          url.searchParams.append("until", until)
        }
        window.location.href = url.toString()
      })
    }

    for (let i = 0; i < bodies.length; i += 1) {
      buildBody(bodies[i], !this.has_run, resultingData[i])
      let name = "chart-container-" + bodies[i].inner
      let title = bodies[i].title

      if (!this.has_run) {
        document.body.appendChild(newChartContainer(name, title))

        this.charts.push({
          chart: newChart(name, title, bodies[i].inner === undefined ? 1 : 2),
          name: name
        })
      }
      this.updateCharts(i, resultingData[i])
    }
    if (!this.has_run) {
      document.getElementById(this.endID).remove()
      this.has_run = true
    }
  }
  updateCharts(id, data) {
    const chart = this.charts[id].chart
    let dp = {}
    const timeMapping = data.mapping.time
    const valueMapping = data.mapping.value
    const innerMapping = data.mapping.inner

    for (const entry of data.values) {
      let dateTime = new Date(entry[timeMapping])

      let curr = {
        x: dateTime,
        y: entry[valueMapping]
      }

      let innerId = entry[innerMapping] === undefined ? 0 : entry[innerMapping] === false ? 1 : 0
      if (dp[innerId] === undefined) {
        dp[innerId] = []
      }
      dp[innerId].push(curr)
    }
    for (const key in dp) {
      chart.options.data[key].dataPoints = dp[key]
    }
    chart.render()
  }

  stop() {
    if (this.interval_id === undefined) {
      return
    }
    clearInterval(this.interval_id)
    this.interval_id = undefined
  }

  start() {
    if (this.interval_id !== undefined) {
      return
    }
    this.interval_id = setInterval(() => this.run(), 1000)
  }
}
