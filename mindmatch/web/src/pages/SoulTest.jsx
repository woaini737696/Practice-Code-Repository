import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores'
import { motion } from 'framer-motion'
import { Sparkles, ArrowLeft, ArrowRight, Check } from 'lucide-react'

export default function SoulTest() {
  const navigate = useNavigate()
  const { updateProfile } = useAuthStore()
  const [currentStep, setCurrentStep] = useState(0)
  const [answers, setAnswers] = useState({})
  const [result, setResult] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const questions = [
    {
      id: 'energy',
      question: '你在社交场合中通常是怎样的？',
      options: [
        { text: '充满活力，享受人群', value: 5 },
        { text: '选择性社交，需要充电时间', value: 3 },
        { text: '安静观察，偶尔参与', value: 2 },
        { text: '独处让我更自在', value: 1 }
      ]
    },
    {
      id: 'social',
      question: '你更倾向于？',
      options: [
        { text: '和一群人一起活动', value: 5 },
        { text: '2-3人的小圈子', value: 4 },
        { text: '一对一的深入交流', value: 2 },
        { text: '大多数时候独处', value: 1 }
      ]
    },
    {
      id: 'thinking',
      question: '你处理问题的方式是？',
      options: [
        { text: '理性分析，关注事实', value: 5 },
        { text: '先想后动，三思而行', value: 4 },
        { text: '跟随直觉，感受先行', value: 2 },
        { text: '随机应变，灵活处理', value: 1 }
      ]
    },
    {
      id: 'planning',
      question: '你更喜欢怎样的生活方式？',
      options: [
        { text: '有计划、有目标', value: 5 },
        { text: '有大致方向，保留弹性', value: 4 },
        { text: '随性而为，享受当下', value: 2 },
        { text: '完全随缘，不做规划', value: 1 }
      ]
    },
    {
      id: 'creativity',
      question: '你更看重什么？',
      options: [
        { text: '创新与可能性', value: 5 },
        { text: '传统与稳定', value: 3 },
        { text: '浪漫与情感', value: 4 },
        { text: '实际与效率', value: 2 }
      ]
    },
    {
      id: 'emotion',
      question: '当面对压力时，你会？',
      options: [
        { text: '和朋友倾诉', value: 5 },
        { text: '独自消化', value: 3 },
        { text: '转移注意力', value: 4 },
        { text: '顺其自然', value: 2 }
      ]
    },
    {
      id: 'values',
      question: '你觉得什么最重要？',
      options: [
        { text: '个人成长', value: 5 },
        { text: '人际关系', value: 4 },
        { text: '内心平静', value: 3 },
        { text: '自由与独立', value: 5 }
      ]
    },
    {
      id: 'dream',
      question: '你的理想生活是？',
      options: [
        { text: '充满挑战与成就', value: 5 },
        { text: '温馨而稳定', value: 3 },
        { text: '自由且随性', value: 4 },
        { text: '简单而充实', value: 2 }
      ]
    }
  ]

  const calculateSoulType = () => {
    const scores = {
      E: 0, I: 0, S: 0, N: 0, T: 0, F: 0, J: 0, P: 0
    }

    Object.values(answers).forEach((value, index) => {
      const dimension = index % 4
      switch (dimension) {
        case 0: value >= 3 ? scores.E++ : scores.I++; break
        case 1: value >= 3 ? scores.S++ : scores.N++; break
        case 2: value >= 3 ? scores.T++ : scores.F++; break
        case 3: value >= 3 ? scores.J++ : scores.P++; break
      }
    })

    return (
      (scores.E > scores.I ? 'E' : 'I') +
      (scores.S > scores.N ? 'S' : 'N') +
      (scores.T > scores.F ? 'T' : 'F') +
      (scores.J > scores.P ? 'J' : 'P')
    )
  }

  const getSoulTags = (type) => {
    const tagMap = {
      'INFP': ['理想主义者', '梦想家', '治愈系'],
      'ENFP': ['热情洋溢', '创意无限', '社交达人'],
      'INTJ': ['思想深邃', '独立自主', '战略家'],
      'ENTP': ['聪明好奇', '善于辩论', '创新者'],
      'ISFJ': ['温柔体贴', '默默付出', '守护者'],
      'ESFJ': ['热情友好', '乐于助人', '社交蝴蝶'],
      'ISTP': ['冷静理性', '动手能力强', '冒险家'],
      'ESTP': ['活在当下', '行动派', '探险家'],
      'INFJ': ['洞察人心', '理想主义', '引路人'],
      'ENFJ': ['魅力领袖', '善于激励', '理想主义者'],
      'INTP': ['逻辑思考', '追求真理', '发明家'],
      'ENTJ': ['果断决策', '领导才能', '指挥官'],
      'ISFP': ['艺术气息', '敏感细腻', '和平主义者'],
      'ESFP': ['活在当下', '充满活力', '表演者'],
      'ISTJ': ['责任感强', '脚踏实地', '守护者'],
      'ESTJ': ['务实高效', '组织能力强', '管理者']
    }
    return tagMap[type] || ['独特灵魂', '正在探索', '无限可能']
  }

  const handleAnswer = (value) => {
    setAnswers({ ...answers, [currentStep]: value })
  }

  const handleNext = () => {
    if (currentStep < questions.length - 1) {
      setCurrentStep(currentStep + 1)
    } else {
      // 提交测试
      const soulType = calculateSoulType()
      const soulTags = getSoulTags(soulType)
      
      setResult({ soulType, soulTags })
    }
  }

  const handleComplete = async () => {
    if (!result) return
    
    setSubmitting(true)
    try {
      await updateProfile({
        soul_type: result.soulType,
        soul_tags: result.soulTags,
        interests: result.soulTags
      })
      navigate('/')
    } catch (error) {
      console.error('保存失败:', error)
    } finally {
      setSubmitting(false)
    }
  }

  if (result) {
    return (
      <div className="min-h-screen flex flex-col">
        <header className="glass px-4 py-3">
          <h1 className="text-lg font-semibold text-center">测试结果</h1>
        </header>

        <main className="flex-1 flex flex-col items-center justify-center p-6">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="text-center"
          >
            <div className="w-32 h-32 mx-auto mb-6 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center animate-pulse-glow">
              <Sparkles className="w-16 h-16 text-white" />
            </div>

            <h2 className="text-4xl font-bold mb-2 gradient-text">{result.soulType}</h2>
            <p className="text-text-secondary mb-6">
              你的灵魂类型是 {result.soulType}
            </p>

            <div className="flex justify-center gap-3 mb-8">
              {result.soulTags.map((tag, i) => (
                <motion.span
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="soul-tag text-sm"
                >
                  {tag}
                </motion.span>
              ))}
            </div>

            <div className="glass-card rounded-2xl p-6 text-left max-w-sm mx-auto mb-8">
              <h3 className="font-semibold mb-3">💫 {result.soulType} 的特点</h3>
              <ul className="text-sm text-text-secondary space-y-2">
                <li>• 善于倾听和理解他人</li>
                <li>• 重视深度而非广度的交流</li>
                <li>• 内心世界丰富而细腻</li>
                <li>• 追求真实的情感连接</li>
              </ul>
            </div>

            <button
              onClick={handleComplete}
              disabled={submitting}
              className="btn-primary w-full max-w-sm"
            >
              {submitting ? '保存中...' : '完成测试'}
            </button>
          </motion.div>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* 顶部 */}
      <header className="glass px-4 py-3 flex items-center">
        <button onClick={() => navigate(-1)} className="p-2 -ml-2">
          <ArrowLeft className="w-6 h-6" />
        </button>
        <h1 className="flex-1 text-center text-lg font-semibold">灵魂测试</h1>
        <div className="w-10" />
      </header>

      {/* 进度条 */}
      <div className="h-1 bg-white/10">
        <div
          className="h-full bg-gradient-to-r from-primary to-secondary transition-all duration-300"
          style={{ width: `${((currentStep + 1) / questions.length) * 100}%` }}
        />
      </div>

      {/* 问题 */}
      <main className="flex-1 flex flex-col items-center justify-center p-6">
        <div className="w-full max-w-sm">
          <p className="text-sm text-text-muted mb-2">
            问题 {currentStep + 1} / {questions.length}
          </p>
          
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
          >
            <h2 className="text-xl font-semibold mb-8">
              {questions[currentStep].question}
            </h2>

            <div className="space-y-3">
              {questions[currentStep].options.map((option, index) => (
                <button
                  key={index}
                  onClick={() => handleAnswer(option.value)}
                  className={`w-full p-4 rounded-xl text-left transition-all ${
                    answers[currentStep] === option.value
                      ? 'bg-primary/30 border-2 border-primary'
                      : 'bg-white/5 border-2 border-transparent hover:border-primary/30'
                  }`}
                >
                  {option.text}
                </button>
              ))}
            </div>
          </motion.div>
        </div>
      </main>

      {/* 底部 */}
      <div className="p-4">
        <button
          onClick={handleNext}
          disabled={answers[currentStep] === undefined}
          className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {currentStep < questions.length - 1 ? (
            <>
              下一题
              <ArrowRight className="w-5 h-5" />
            </>
          ) : (
            <>
              <Check className="w-5 h-5" />
              查看结果
            </>
          )}
        </button>
      </div>
    </div>
  )
}
