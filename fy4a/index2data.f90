
subroutine index2data(TB,l,c,l_lat,l_lon,ll,nn,TBB)
!f2py intent(in) :: TB,l,c,l_lat,l_lon,ll,nn
!f2py intent(out):: TBB
implicit none

integer :: l_lat,l_lon,ll,nn
integer :: l(l_lat,l_lon),c(l_lat,l_lon)
real*8  :: TBB(l_lat,l_lon)
real*8  :: TB(ll,nn)

integer i,j

TBB(1:l_lat,1:l_lon)=-1

do i=1,l_lat
    do j=1,l_lon
        if ((l(i,j)>=0) .and. (c(i,j)>=0)) then
            TBB(i,j)=TB(l(i,j)+1,c(i,j)+1)
        end if
    end do
end do

end subroutine index2data

subroutine cal2data(data0,cal,l_lat,l_lon,TBB)
!f2py intent(in) :: data0,cal,l_lat,l_lon
!f2py intent(out):: TBB
implicit none

integer :: l_lat,l_lon
real*8  :: cal(4096)
integer  :: data0(l_lat,l_lon)
real*8  :: TBB(l_lat,l_lon)

integer i,j

TBB(1:l_lat,1:l_lon)=-1

do i=1,l_lat
    do j=1,l_lon
        if ((data0(i,j)<4096) .and. (data0(i,j)>=0)) then
            TBB(i,j)=cal(data0(i,j)+1)
        end if
    end do
end do

end subroutine cal2data

subroutine cal2data_07(data0,cal,l_lat,l_lon,TBB)
!f2py intent(in) :: data0,cal,l_lat,l_lon
!f2py intent(out):: TBB
implicit none

integer :: l_lat,l_lon
real*8  :: cal(65536)
integer  :: data0(l_lat,l_lon)
real*8  :: TBB(l_lat,l_lon)

integer i,j

TBB(1:l_lat,1:l_lon)=-1

do i=1,l_lat
    do j=1,l_lon
        if ((data0(i,j)<65536) .and. (data0(i,j)>=0)) then
            TBB(i,j)=cal(data0(i,j)+1)
        end if
    end do
end do

end subroutine cal2data_07

