'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  LogOut,
  Trash2,
  Download,
  Info,
  Eye,
  Sprout,
  Flame,
  Bell,
  FlaskConical,
  ChevronRight,
  Smartphone,
} from 'lucide-react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from '@/components/ui/accordion';
import {
  AlertDialog,
  AlertDialogTrigger,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogAction,
  AlertDialogCancel,
} from '@/components/ui/alert-dialog';
import { toast } from 'sonner';
import { useNabomStore } from '@/store/nabom-store';
import type { ReflectionIntensity } from '@/types/nabom';

// ─── Animation Helpers ───────────────────────────────────────────────────────

const noMotion = () =>
  typeof window !== 'undefined' &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const fadeUp = (delay = 0) => {
  if (noMotion()) return {};
  return {
    initial: { opacity: 0, y: 16 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.5, delay, ease: [0.22, 1, 0.36, 1] as const },
  };
};

// ─── Intensity Option Config ─────────────────────────────────────────────────

interface IntensityOption {
  value: ReflectionIntensity;
  label: string;
  description: string;
  icon: React.ReactNode;
}

const INTENSITY_OPTIONS: IntensityOption[] = [
  {
    value: 'reflect',
    label: '해석 중심',
    description: '행동 제안 최소',
    icon: <Eye className="h-5 w-5" />,
  },
  {
    value: 'grow',
    label: '기본값',
    description: '작은 행동 실험 제안',
    icon: <Sprout className="h-5 w-5" />,
  },
  {
    value: 'challenge',
    label: '도전적',
    description: '반복되는 회피를 적극적으로 지적',
    icon: <Flame className="h-5 w-5" />,
  },
];

// ─── Main Component ──────────────────────────────────────────────────────────

export default function Settings() {
  const {
    reflectionIntensity,
    setReflectionIntensity,
    setView,
    openLegal,
    session,
    logout,
    exportData,
    deleteAccountViaApi,
    deleteRecordsViaApi,
    settingsBusy,
  } = useNabomStore();

  const [weeklyNotif, setWeeklyNotif] = useState(true);
  const [experimentReminder, setExperimentReminder] = useState(true);

  const devices = useNabomStore((s) => s.devices);
  const devicesLimit = useNabomStore((s) => s.devicesLimit);
  const loadDevices = useNabomStore((s) => s.loadDevices);
  const revokeDevice = useNabomStore((s) => s.revokeDevice);

  useEffect(() => {
    void loadDevices();
  }, [loadDevices]);

  const handleRevokeDevice = async (deviceId: string) => {
    const ok = await revokeDevice(deviceId);
    if (ok) toast.success('기기 등록이 해제되었어요.');
    else toast.error('기기를 해제하지 못했어요. 잠시 후 다시 시도해주세요.');
  };

  const handleLogout = () => {
    logout();
    toast.success('로그아웃되었어요.');
  };

  const handleExport = async () => {
    const ok = await exportData();
    if (ok) toast.success('데이터를 내보냈어요.');
    else toast.error('데이터를 내보내지 못했어요. 잠시 후 다시 시도해주세요.');
  };

  const handleDeleteAccount = async () => {
    const ok = await deleteAccountViaApi();
    if (ok) toast.success('계정과 모든 기록이 삭제되었어요. 또 만나요.');
    else toast.error('계정을 삭제하지 못했어요. 잠시 후 다시 시도해주세요.');
  };

  const handleDeleteRecords = async () => {
    const ok = await deleteRecordsViaApi();
    if (ok) toast.success('기록이 삭제되었어요.');
    else toast.error('기록을 삭제하지 못했어요. 잠시 후 다시 시도해주세요.');
  };

  return (
    <main className="min-h-screen flex flex-col bg-background">
      <div className="nabom-page">
        {/* ── Header ─────────────────────────────────────────────────────── */}
        <motion.div {...fadeUp(0)} className="mb-5">
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            설정
          </h1>
        </motion.div>

        <div className="md:grid md:grid-cols-2 md:items-start md:gap-8">
          <div>

        {/* ── 계정 (Account) ─────────────────────────────────────────────── */}
        <motion.div {...fadeUp(0.05)} className="mb-5">
          <Card className="border-border/50 shadow-sm">
            <CardHeader>
              <CardTitle className="text-base">계정</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Nickname (read-only) */}
              <div className="flex items-center justify-between min-h-[44px]">
                <span className="text-sm text-foreground">닉네임</span>
                <span className="text-sm text-muted-foreground font-medium">
                  {session?.nickname || '사용자'}
                </span>
              </div>

              <Separator />

              {/* Email (read-only) */}
              <div className="flex items-center justify-between min-h-[44px]">
                <span className="text-sm text-foreground">이메일</span>
                <span className="text-sm text-muted-foreground font-medium">
                  {session?.email || '-'}
                </span>
              </div>

              <Separator />

              {/* Logout */}
              <button
                type="button"
                className="flex w-full items-center justify-between min-h-[44px] text-left text-sm text-foreground hover:text-primary transition-colors"
                onClick={handleLogout}
              >
                <div className="flex items-center gap-3">
                  <LogOut className="h-4 w-4 text-muted-foreground" />
                  <span>로그아웃</span>
                </div>
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              </button>

              <Separator />

              {/* Withdraw */}
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <button
                    type="button"
                    className="flex w-full items-center justify-between min-h-[44px] text-left text-sm text-destructive hover:text-destructive/80 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <Trash2 className="h-4 w-4" />
                      <span>회원 탈퇴</span>
                    </div>
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>정말 탈퇴하시겠어요?</AlertDialogTitle>
                    <AlertDialogDescription className="text-sm leading-relaxed">
                      탈퇴하시면 모든 기록, 프로필, 분석 데이터가 영구적으로
                      삭제됩니다. 이 작업은 되돌릴 수 없습니다.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel className="min-h-[44px]">취소</AlertDialogCancel>
                    <AlertDialogAction
                      className="min-h-[44px] bg-destructive text-white hover:bg-destructive/90"
                      onClick={handleDeleteAccount}
                    >
                      {settingsBusy ? '삭제 중…' : '탈퇴하기'}
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </CardContent>
          </Card>
        </motion.div>

        {/* ── 알림 설정 (Notifications) ─────────────────────────────────── */}
        <motion.div {...fadeUp(0.1)} className="mb-5">
          <Card className="border-border/50 shadow-sm">
            <CardHeader>
              <CardTitle className="text-base">알림 설정</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between min-h-[44px]">
                <div className="flex items-center gap-3">
                  <Bell className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <p className="text-sm font-medium text-foreground">주간 회고 준비 알림</p>
                    <p className="text-xs text-muted-foreground">일주일이 끝날 때 회고를 준비해 드려요</p>
                  </div>
                </div>
                <Switch
                  checked={weeklyNotif}
                  onCheckedChange={setWeeklyNotif}
                  aria-label="주간 회고 준비 알림"
                />
              </div>

              <Separator />

              <div className="flex items-center justify-between min-h-[44px]">
                <div className="flex items-center gap-3">
                  <FlaskConical className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <p className="text-sm font-medium text-foreground">성장 실험 리마인더</p>
                    <p className="text-xs text-muted-foreground">진행 중인 실험을 알려드려요</p>
                  </div>
                </div>
                <Switch
                  checked={experimentReminder}
                  onCheckedChange={setExperimentReminder}
                  aria-label="성장 실험 리마인더"
                />
              </div>
            </CardContent>
          </Card>
        </motion.div>
          </div>
          <div>

        {/* ── 기기 관리 (Devices) ───────────────────────────────────────── */}
        <motion.div {...fadeUp(0.15)} className="mb-5">
          <Card className="border-border/50 shadow-sm">
            <CardHeader>
              <CardTitle className="text-base">내 기기</CardTitle>
              <CardDescription>
                로그인된 기기예요. 다른 기기에서 접속하지 못하게 하려면 여기서 해제하세요.
                (계정당 최대 {devicesLimit}대)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {devices.length === 0 ? (
                <p className="text-sm text-muted-foreground">등록된 기기가 없어요.</p>
              ) : (
                devices.map((device) => (
                  <div
                    key={device.deviceId}
                    className="flex items-center justify-between gap-3 rounded-xl border border-border/60 bg-card p-4"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <Smartphone className="h-4 w-4 shrink-0 text-muted-foreground" />
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-foreground truncate">
                          {device.label}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {device.lastSeen ? `마지막 접속 ${device.lastSeen.slice(0, 10)}` : ''}
                        </p>
                      </div>
                    </div>
                    <button
                      type="button"
                      className="shrink-0 text-xs font-medium text-destructive hover:text-destructive/80 transition-colors min-h-[44px] px-2"
                      onClick={() => void handleRevokeDevice(device.deviceId)}
                    >
                      해제
                    </button>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* ── 회고 강도 (Reflection Intensity) ──────────────────────────── */}
        <motion.div {...fadeUp(0.18)} className="mb-5">
          <Card className="border-border/50 shadow-sm">
            <CardHeader>
              <CardTitle className="text-base">회고 강도</CardTitle>
              <CardDescription>
                AI 분석이 얼마나 적극적으로 피드백을 줄지 선택하세요
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 gap-3">
                {INTENSITY_OPTIONS.map((option) => {
                  const isActive = reflectionIntensity === option.value;
                  return (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => setReflectionIntensity(option.value)}
                      className={`flex items-center gap-4 rounded-xl border p-4 text-left transition-all min-h-[44px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                        isActive
                          ? 'border-primary bg-warm-50 ring-1 ring-primary/20'
                          : 'border-border/60 bg-card hover:bg-muted/50'
                      }`}
                      aria-pressed={isActive}
                    >
                      <div
                        className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg transition-colors ${
                          isActive
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-muted text-muted-foreground'
                        }`}
                      >
                        {option.icon}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p
                          className={`text-sm font-semibold ${
                            isActive ? 'text-foreground' : 'text-foreground/80'
                          }`}
                        >
                          {option.label}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {option.description}
                        </p>
                      </div>
                      {isActive && (
                        <Badge variant="default" className="shrink-0 text-xs">
                          선택됨
                        </Badge>
                      )}
                    </button>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* ── 데이터 관리 (Data Management) ──────────────────────────────── */}
        <motion.div {...fadeUp(0.2)} className="mb-5">
          <Card className="border-border/50 shadow-sm">
            <CardHeader>
              <CardTitle className="text-base">데이터 관리</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Export */}
              <Button
                variant="outline"
                className="w-full min-h-[44px] justify-start gap-3 text-sm font-medium"
                disabled={settingsBusy}
                onClick={handleExport}
              >
                <Download className="h-4 w-4 text-muted-foreground" />
                데이터 내보내기
              </Button>

              <Separator />

              {/* Delete records */}
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button
                    variant="outline"
                    className="w-full min-h-[44px] justify-start gap-3 text-sm font-medium text-destructive hover:text-destructive border-destructive/30 hover:border-destructive/50 hover:bg-destructive/5"
                  >
                    <Trash2 className="h-4 w-4" />
                    기록 삭제
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>기록을 삭제하시겠어요?</AlertDialogTitle>
                    <AlertDialogDescription className="text-sm leading-relaxed">
                      삭제된 기록은 AI 분석에서도 제외됩니다.
                      이 작업은 되돌릴 수 없습니다.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel className="min-h-[44px]">
                      취소
                    </AlertDialogCancel>
                    <AlertDialogAction
                      className="min-h-[44px] bg-destructive text-white hover:bg-destructive/90"
                      onClick={handleDeleteRecords}
                    >
                      {settingsBusy ? '삭제 중…' : '삭제하기'}
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>

              <p className="text-xs text-muted-foreground leading-relaxed">
                삭제된 기록은 AI 분석에서도 제외됩니다.
              </p>
            </CardContent>
          </Card>
        </motion.div>

        {/* ── 분석 방법 고지 (Transparency) ───────────────────────────────── */}
        <motion.div {...fadeUp(0.25)} className="mb-5">
          <Card className="border-border/50 shadow-sm">
            <CardHeader>
              <CardTitle className="text-base">분석 방법 고지</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <Accordion type="single" collapsible className="w-full">
                <AccordionItem value="transparency" className="border-0 px-6">
                  <AccordionTrigger className="text-sm text-foreground hover:no-underline py-4">
                    <div className="flex items-center gap-2">
                      <Info className="h-4 w-4 text-muted-foreground" />
                      나봄의 분석은 어떻게 이루어지나요?
                    </div>
                  </AccordionTrigger>
                  <AccordionContent>
                    <div className="space-y-3 pb-2">
                      <div className="flex items-start gap-2.5 rounded-lg bg-warm-50/60 px-3 py-2.5">
                        <div className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-warm-400" />
                        <p className="text-sm leading-relaxed text-foreground/80">
                          나봄은 출생정보 기반 전통 명리 체계가 초기 가설에 포함됩니다.
                        </p>
                      </div>
                      <div className="flex items-start gap-2.5 rounded-lg bg-warm-50/60 px-3 py-2.5">
                        <div className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-warm-400" />
                        <p className="text-sm leading-relaxed text-foreground/80">
                          하지만 시간이 지날수록 실제 삶의 기록이 분석에 더 큰 비중을
                          차지합니다.
                        </p>
                      </div>
                      <div className="flex items-start gap-2.5 rounded-lg bg-warm-50/60 px-3 py-2.5">
                        <div className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-warm-400" />
                        <p className="text-sm leading-relaxed text-foreground/80">
                          최종 판단은 사용자의 기록과 피드백을 바탕으로 이루어집니다.
                        </p>
                      </div>
                    </div>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </CardContent>
          </Card>
        </motion.div>

        {/* ── 이용 안내 (App Info) ───────────────────────────────────────── */}
        <motion.div {...fadeUp(0.3)} className="mb-5">
          <Card className="border-border/50 shadow-sm">
            <CardHeader>
              <CardTitle className="text-base">이용 안내</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between min-h-[44px]">
                <span className="text-sm text-foreground">버전 정보</span>
                <Badge variant="outline" className="font-mono text-xs">
                  나봄 v0.1 (Phase 1 Alpha)
                </Badge>
              </div>

              <Separator />

              <button
                type="button"
                className="flex w-full items-center justify-between min-h-[44px] text-left text-sm text-foreground hover:text-primary transition-colors"
                onClick={() => openLegal('terms')}
              >
                <span>이용약관</span>
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              </button>

              <Separator />

              <button
                type="button"
                className="flex w-full items-center justify-between min-h-[44px] text-left text-sm text-foreground hover:text-primary transition-colors"
                onClick={() => openLegal('privacy')}
              >
                <span>개인정보처리방침</span>
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              </button>

              <Separator />

              <button
                type="button"
                className="flex w-full items-center justify-between min-h-[44px] text-left text-sm text-foreground hover:text-primary transition-colors"
                onClick={() => setView('admin')}
              >
                <span>운영 현황</span>
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              </button>
            </CardContent>
          </Card>
        </motion.div>
          </div>
        </div>
      </div>
    </main>
  );
}
