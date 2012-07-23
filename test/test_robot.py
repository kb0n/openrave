# -*- coding: utf-8 -*-
# Copyright (C) 2011 Rosen Diankov <rosen.diankov@gmail.com>
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from common_test_openrave import *

class RunRobot(EnvironmentSetup):
    def __init__(self,collisioncheckername):
        self.collisioncheckername = collisioncheckername
    def setup(self):
        EnvironmentSetup.setup(self)
        self.env.SetCollisionChecker(RaveCreateCollisionChecker(self.env,self.collisioncheckername))

    def test_dualarm_grabbing(self):
        with self.env:
            robot = self.LoadRobot('robots/schunk-lwa3-dual.robot.xml')
            body = self.env.ReadKinBodyXMLFile('data/box3.kinbody.xml')
            self.env.Add(body)
            T = eye(4)
            T[1,3] = -1.18
            T[2,3] = 0.712
            body.SetTransform(T)
            robot.SetActiveManipulator('leftarm')
            assert(self.env.CheckCollision(robot))
            robot.Grab(body)
            assert(not self.env.CheckCollision(robot))
            robot.SetDOFValues(array([  0.00000000e+00,  -1.43329144e+00,  -3.99190831e-15, -1.86732388e+00,   5.77239752e-01,  -3.37631690e-07, 6.67713991e-08,   0.00000000e+00,  -1.70089030e+00, -6.42544150e-01,  -1.25030589e+00,  -3.33493233e-08, -5.58212676e-08,   1.60115015e-08]))
            assert(robot.CheckSelfCollision())

    def test_basic(self):
        with self.env:
            for robotfile in g_robotfiles:
                self.env.Reset()
                robot = self.LoadRobot(robotfile)
                assert(robot.GetDOF() == robot.GetActiveDOF())
                assert(robot.GetLinks()[0].GetParent().GetActiveDOF() == robot.GetActiveDOF())

    def test_collisionmaprobot(self):
        env=self.env
        xml = """<environment>
<robot file="robots/collisionmap.robot.xml">
</robot>
</environment>
"""
        self.LoadDataEnv(xml)
        with env:
            robot=env.GetRobots()[0]
            assert(robot.GetXMLId().lower()=='collisionmaprobot')
            robot.SetDOFValues([9/180.0*pi,1/180.0*pi],[1,2])
            assert(robot.CheckSelfCollision())
            robot.SetDOFValues([0/180.0*pi,1/180.0*pi],[1,2])
            assert(not robot.CheckSelfCollision())
            env.Reset()
            robot=self.LoadRobot('robots/collisionmap.robot.xml')
            assert(robot.GetXMLId().lower()=='collisionmaprobot')

    def test_grabcollision(self):
        env=self.env
        self.LoadEnv('robots/man1.zae') # load a simple scene
        with env:
            robot = env.GetRobots()[0] # get the first robot
            leftarm = robot.GetManipulator('leftarm')
            rightarm = robot.GetManipulator('rightarm')

            self.LoadEnv('data/mug1.kinbody.xml'); 
            leftmug = env.GetKinBody('mug')
            self.LoadEnv('data/mug2.kinbody.xml')
            rightmug = env.GetKinBody('mug2')

            env.StopSimulation()
            leftMugGrabPose = array([[ 0.99516672, -0.0976999 ,  0.00989374,  0.14321238],
                                     [ 0.09786028,  0.99505007, -0.01728364,  0.94120538],
                                     [-0.00815616,  0.01816831,  0.9998017 ,  0.38686624],
                                     [ 0.        ,  0.        ,  0.        ,  1.        ]])
            leftmug.SetTransform(leftMugGrabPose)
            rightMugGrabPose = array([[  9.99964535e-01,  -1.53668225e-08,   8.41848925e-03, -1.92047462e-01],
                                      [ -8.40134174e-03,  -6.37951940e-02,   9.97927606e-01, 9.22815084e-01],
                                      [  5.37044369e-04,  -9.97963011e-01,  -6.37929291e-02, 4.16847348e-01],
                                      [  0.00000000e+00,   0.00000000e+00,   0.00000000e+00, 1.00000000e+00]])
            rightmug.SetTransform(rightMugGrabPose);
            assert(not env.CheckCollision(leftmug,rightmug))
            
            grabJointAngles = array([ -3.57627869e-07,   0.00000000e+00,  -1.46997878e-15, -1.65528119e+00,  -1.23030146e-08,  -8.41909389e-11, 0.00000000e+00], dtype=float32)

            robot.SetDOFValues(grabJointAngles,rightarm.GetArmIndices())
            robot.SetDOFValues(grabJointAngles,leftarm.GetArmIndices())
            
            robot.SetActiveManipulator(rightarm)
            robot.Grab(rightmug)
            robot.SetActiveManipulator(leftarm)
            robot.Grab(leftmug)

            assert(not robot.CheckSelfCollision())
            assert(not env.CheckCollision(robot))

            self.log.debug('Now changing arm joint angles so that the two mugs collide. The checkSelfCollision returns:')
            collisionJointAngles = array([ -2.38418579e-07,   0.00000000e+00,  -2.96873480e-01, -1.65527940e+00,  -3.82479293e-08,  -1.23165381e-10, 1.35525272e-20]);
            robot.SetDOFValues(collisionJointAngles,rightarm.GetArmIndices())
            robot.SetDOFValues(collisionJointAngles,leftarm.GetArmIndices())
            assert(robot.CheckSelfCollision())
            assert(not env.CheckCollision(robot))

            robot.ReleaseAllGrabbed()
            assert(env.CheckCollision(leftmug,rightmug))        

    def test_grabcollision_dynamic(self):
        self.log.info('test if can handle grabbed bodies being enabled/disabled')
        env=self.env
        robot = self.LoadRobot('robots/barrettwam.robot.xml')
        with env:
            target = env.ReadKinBodyURI('data/mug1.kinbody.xml')
            env.Add(target,True)
            manip=robot.GetActiveManipulator()
            target.SetTransform(manip.GetEndEffector().GetTransform())
            assert(env.CheckCollision(robot,target))
            self.log.info('check disabling target')
            target.Enable(False)
            robot.Grab(target,manip.GetEndEffector())
            assert(not robot.CheckSelfCollision())
            target.Enable(True)
            assert(not robot.CheckSelfCollision())
            target.Enable(False)
            assert(not robot.CheckSelfCollision())
            target.GetLinks()[0].Enable(True)
            assert(not robot.CheckSelfCollision())
            self.log.info('check disabling links')
            robot.Enable(False)
            assert(not robot.CheckSelfCollision())
            robot.RegrabAll()
            assert(not robot.CheckSelfCollision())
            robot.Enable(True)
            assert(not robot.CheckSelfCollision())
            
    def test_ikcollision(self):
        self.log.info('test if can solve IK during collisions')
        env=self.env
        with env:
            robot = self.LoadRobot('robots/pr2-beta-static.zae')
            target = env.ReadKinBodyURI('data/mug1.kinbody.xml')
            env.Add(target,True)
            T=target.GetTransform()
            T[0:3,3] = [-0.342,0,0.8]
            target.SetTransform(T)
            floor = RaveCreateKinBody(env,'')
            floor.InitFromBoxes(array([[0,0,0,2,2,0.01]]),True)
            floor.SetName('floor')
            env.Add(floor,True)
            
            assert(env.CheckCollision(robot))
            manip=robot.SetActiveManipulator('leftarm')
            manip2 = robot.GetManipulator('rightarm')
            robot.SetActiveDOFs(manip.GetArmIndices())
            assert(not manip.CheckEndEffectorCollision(manip.GetTransform()))
            assert(not manip2.CheckEndEffectorCollision(manip2.GetTransform()))
            assert(not manip.CheckEndEffectorCollision(manip.GetIkParameterization(IkParameterizationType.Transform6D)))
            assert(not manip2.CheckEndEffectorCollision(manip2.GetIkParameterization(IkParameterizationType.Transform6D)))

            # with bullet, robot gets into self-collision when first angle reaches 0.5
            robot.SetActiveDOFValues([0.678, 0, 1.75604762, -1.74228108, 0, 0, 0])
            assert(not robot.CheckSelfCollision())
            Tmanip = manip.GetTransform()
            robot.SetActiveDOFValues(zeros(robot.GetActiveDOF()))
            assert(manip.FindIKSolution(Tmanip,IkFilterOptions.CheckEnvCollisions) is not None)

            basemanip = interfaces.BaseManipulation(robot)
            out=basemanip.MoveToHandPosition(matrices=[Tmanip],execute=False)
            assert(out is not None)
            
            # self colliding
            robot.SetActiveDOFValues([  2.20622614e-01,   0.00000000e+00,   1.75604762e+00, -1.74228108e+00,   0.00000000e+00,  -9.56775092e-16, 0.00000000e+00])
            assert(robot.CheckSelfCollision())
            Tmanip = manip.GetTransform()
            robot.SetActiveDOFValues(zeros(robot.GetActiveDOF()))
            assert(manip.FindIKSolution(Tmanip,IkFilterOptions.CheckEnvCollisions) is None)
            assert(manip.FindIKSolution(Tmanip,IkFilterOptions.CheckEnvCollisions|IkFilterOptions.IgnoreEndEffectorCollisions) is not None)
            assert(not manip.CheckEndEffectorCollision(Tmanip))

            box = RaveCreateKinBody(env,'')
            box.InitFromBoxes(array([[0,0,0,0.05,0.05,0.2]]),True)
            box.SetName('box')
            env.Add(box,True)
            box.SetTransform(manip.GetTransform())
            robot.Grab(box)
            robot.SetActiveDOFValues([  0.5,   0.00000000e+00,   1.57, -1.74228108e+00,   3.23831570e-16,   0.00000000e+00, 0.00000000e+00])
            assert(robot.CheckSelfCollision())
            Tmanip = manip.GetTransform()
            robot.SetActiveDOFValues(zeros(robot.GetActiveDOF()))

            assert(not robot.CheckSelfCollision())
            assert(manip.FindIKSolution(Tmanip,IkFilterOptions.CheckEnvCollisions|IkFilterOptions.IgnoreEndEffectorCollisions) is not None)
            assert(not robot.CheckSelfCollision())
            assert(not manip.CheckEndEffectorCollision(Tmanip))

            robot.SetActiveDOFValues([ 0.00000000e+00,   0.858,   2.95911693e+00, -0.1,   0.00000000e+00,  -3.14018492e-16, 0.00000000e+00])
            Tmanip = manip.GetTransform()

            assert(manip.FindIKSolution(Tmanip,IkFilterOptions.CheckEnvCollisions|IkFilterOptions.IgnoreEndEffectorCollisions) is not None)
            # test if initial colliding attachments are handled correctly
            robot.SetActiveDOFValues(zeros(robot.GetActiveDOF()))
            T = manip.GetTransform()
            T[0,3] += 0.2
            target.SetTransform(T)
            assert(not robot.CheckSelfCollision())
            assert(env.CheckCollision(box,target))
            assert(manip.CheckEndEffectorCollision(manip.GetTransform()))
            assert(not manip2.CheckEndEffectorCollision(manip2.GetTransform()))
            robot.Grab(target)
            assert(robot.IsGrabbing(target))
            assert(not robot.CheckSelfCollision())
            robot.RegrabAll()
            assert(not robot.CheckSelfCollision())

            robot.Release(target)
            assert(not robot.IsGrabbing(target))
            
            box2 = RaveCreateKinBody(env,'')
            box2.InitFromBoxes(array([[0,0,0,0.05,0.05,0.2]]),True)
            box2.SetName('box2')
            env.Add(box2,True)
            box2.SetTransform(manip2.GetTransform())
            robot.Grab(box2,grablink=manip2.GetEndEffector())
            assert(not manip2.CheckEndEffectorCollision(manip2.GetTransform()))

            robot.Grab(target)
            Tmanip = manip.GetTransform()
            assert(not manip.CheckEndEffectorCollision(Tmanip))
            robot.SetActiveDOFValues([ 0.00000000e+00,   0.858,   2.95911693e+00, -1.57009246e-16,   0.00000000e+00,  -3.14018492e-16, 0.00000000e+00])
            assert(not manip.CheckEndEffectorCollision(Tmanip))

    def test_checkendeffector(self):
        self.log.info('test if can check end effector collisions with ik params')
        env=self.env
        self.LoadEnv('data/katanatable.env.xml')
        robot=env.GetRobots()[0]
        ikmodel = databases.inversekinematics.InverseKinematicsModel(robot, iktype=IkParameterization.Type.TranslationDirection5D)
        if not ikmodel.load():
            ikmodel.autogenerate()
            
        with env:
            robot.SetActiveDOFs(ikmodel.manip.GetArmIndices())
            robot.SetActiveDOFValues([ 0,  0.89098841,  0.92174268, -1.32022237,  0])
            ikparam=ikmodel.manip.GetIkParameterization(IkParameterizationType.TranslationDirection5D)
            assert(not env.CheckCollision(robot))
            robot.SetActiveDOFValues(zeros(robot.GetActiveDOF()))
            assert(not ikmodel.manip.CheckEndEffectorCollision(ikparam))

            T = eye(4)
            T[2,3] = -0.1
            ikparam2 = IkParameterization(ikparam)
            ikparam2.MultiplyTransform(T)
            assert(ikmodel.manip.FindIKSolution(ikparam2,0) is not None)
            assert(ikmodel.manip.FindIKSolution(ikparam2,IkFilterOptions.CheckEnvCollisions) is None)
            assert(ikmodel.manip.CheckEndEffectorCollision(ikparam2))
            assert(ikmodel.manip.FindIKSolution(ikparam2,IkFilterOptions.CheckEnvCollisions|IkFilterOptions.IgnoreEndEffectorCollisions) is not None)

        ikmodel = databases.inversekinematics.InverseKinematicsModel(robot, iktype=IkParameterization.Type.Translation3D)
        if not ikmodel.load():
            ikmodel.autogenerate()

        with env:
            robot.SetActiveDOFs(ikmodel.manip.GetArmIndices())
            robot.SetActiveDOFValues([ 0,  0.89098841,  0.92174268, -1.32022237,  0])
            ikparam=ikmodel.manip.GetIkParameterization(IkParameterizationType.Translation3D)
            robot.SetActiveDOFValues(zeros(robot.GetActiveDOF()))
            try:
                ikmodel.manip.CheckEndEffectorCollision(ikparam)
                raise ValueError('expected exception')
            
            except openrave_exception:
                pass

            T = eye(4)
            T[2,3] = -0.1
            ikparam2 = IkParameterization(ikparam)
            ikparam2.MultiplyTransform(T)
            assert(ikmodel.manip.FindIKSolution(ikparam2,0) is not None)
            assert(ikmodel.manip.FindIKSolution(ikparam2,IkFilterOptions.CheckEnvCollisions) is None)
            assert(ikmodel.manip.FindIKSolution(ikparam2,IkFilterOptions.CheckEnvCollisions|IkFilterOptions.IgnoreEndEffectorCollisions) is not None)

    def test_badtrajectory(self):
        self.log.info('create a discontinuous trajectory and check if robot throws exception')
        env=self.env
        robot=self.LoadRobot('robots/mitsubishi-pa10.zae')
        with env:
            orgvalues = robot.GetActiveDOFValues()
            lower,upper = robot.GetDOFLimits()
            traj=RaveCreateTrajectory(env,'')
            traj.Init(robot.GetActiveConfigurationSpecification())
            traj.Insert(0,r_[orgvalues,upper+0.1])
            assert(traj.GetNumWaypoints()==2)
            try:
                planningutils.RetimeActiveDOFTrajectory(traj,robot,False)
                self.RunTrajectory(robot,traj)
                raise ValueError('controller did not throw limit expected exception!')
            
            except Exception, e:
                pass

            traj.Init(robot.GetActiveConfigurationSpecification())
            traj.Insert(0,r_[lower,upper])
            assert(traj.GetNumWaypoints()==2)
            try:
                planningutils.RetimeActiveDOFTrajectory(traj,robot,False,maxvelmult=10)
                self.RunTrajectory(robot,traj)
                raise ValueError('controller did not throw velocity limit expected exception!')
            
            except Exception, e:
                pass

    def test_bigrange(self):
        env=self.env
        robot=self.LoadRobot('robots/kuka-kr5-r650.zae')
        ikmodel = databases.inversekinematics.InverseKinematicsModel(robot, iktype=IkParameterization.Type.Transform6D)
        if not ikmodel.load():
            ikmodel.autogenerate()

        with env:
            j=robot.GetJointFromDOFIndex(ikmodel.manip.GetArmIndices()[-1])
            lower,upper = j.GetLimits()
            assert( upper-lower > 3*pi )
            robot.SetDOFValues(lower+0.1,[j.GetDOFIndex()])
            assert(transdist(robot.GetDOFValues([j.GetDOFIndex()]),lower+0.1) <= g_epsilon)

            robot.SetDOFValues(ones(len(ikmodel.manip.GetArmIndices())),ikmodel.manip.GetArmIndices(),True)
            ikparam = ikmodel.manip.GetIkParameterization(IkParameterization.Type.Transform6D)
            sols = ikmodel.manip.FindIKSolutions(ikparam,IkFilterOptions.CheckEnvCollisions)
            assert(len(sols)==8)

            # add a filter
            numrepeats = [0]
            indices = []
            def customfilter(solution, manip, ikparam):
                out = manip.GetIkSolver().SendCommand('GetRobotLinkStateRepeatCount')
                if out=='1':
                    numrepeats[0] += 1
                out = manip.GetIkSolver().SendCommand('GetSolutionIndices')
                for index in out.split()[1:]:
                    indices.append(int(index))
                return IkReturnAction.Success
            
            handle = ikmodel.manip.GetIkSolver().RegisterCustomFilter(0,customfilter)
            sols = ikmodel.manip.FindIKSolutions(ikparam,IkFilterOptions.CheckEnvCollisions)
            assert(len(sols)==8)
            assert(numrepeats[0]==4)
            indices.sort()
            assert(indices == [0,3,4,7,0x20000,0x20003,0x20004,0x20007])
            handle.Close()
            # customfilter shouldn't be executed anymore
            sols = ikmodel.manip.FindIKSolutions(ikparam,IkFilterOptions.CheckEnvCollisions)
            assert(numrepeats[0]==4)

    def test_manipulators(self):
        env=self.env
        robot=self.LoadRobot('robots/pr2-beta-static.zae')
        manip=robot.GetManipulator('leftarm_torso')
        links = manip.GetChildLinks()
        assert(all([l.GetName().startswith('l_gripper') or l.GetName() == 'l_wrist_roll_link' for l in links]))
        ilinks = manip.GetIndependentLinks()
        expectednames = set([u'base_footprint', u'base_link', u'base_bellow_link', u'base_laser_link', u'bl_caster_rotation_link', u'bl_caster_l_wheel_link', u'bl_caster_r_wheel_link', u'br_caster_rotation_link', u'br_caster_l_wheel_link', u'br_caster_r_wheel_link', u'fl_caster_rotation_link', u'fl_caster_l_wheel_link', u'fl_caster_r_wheel_link', u'fr_caster_rotation_link', u'fr_caster_l_wheel_link', u'fr_caster_r_wheel_link', u'torso_lift_motor_screw_link'])
        curnames = set([l.GetName() for l in ilinks])
        assert(expectednames==curnames)
        cjoints = manip.GetChildJoints()
        assert(len(cjoints)==4)
        assert(all([j.GetName().startswith('l_') for j in cjoints]))
        cdofs = manip.GetChildDOFIndices()
        assert(cdofs == [22,23,24,25])        

    def test_grabdynamics(self):
        self.log.info('test is grabbed bodies have correct')
        env=self.env
        with env:
            robot=self.LoadRobot('robots/pr2-beta-static.zae')
            body = env.ReadKinBodyURI('data/mug1.kinbody.xml')
            env.Add(body)
            manip=robot.SetActiveManipulator('leftarm')
            velocities = zeros(robot.GetDOF())
            velocities[manip.GetArmIndices()] = ones(len(manip.GetArmIndices()))
            robot.SetDOFVelocities(velocities)
            Tmanip = manip.GetTransform()
            Tbody = array(Tmanip)
            Tbody[0,3] += 0.1
            body.SetTransform(Tbody)
            robot.Grab(body)
            diff = Tbody[0:3,3] - Tmanip[0:3,3]
            bodyvelocity = body.GetLinkVelocities()[0]
            manipvelocity = manip.GetVelocity()
            assert(transdist(manipvelocity[0:3] + cross(manipvelocity[3:6],diff),bodyvelocity[0:3]) <= g_epsilon)
            assert(transdist(manipvelocity[3:6],bodyvelocity[3:6]) <= g_epsilon)
            
            # change velocity and try again
            velocities[manip.GetArmIndices()] = -ones(len(manip.GetArmIndices()))
            robot.SetDOFVelocities(velocities)
            bodyvelocity = body.GetLinkVelocities()[0]
            manipvelocity = manip.GetVelocity()
            assert(transdist(manipvelocity[0:3] + cross(manipvelocity[3:6],diff),bodyvelocity[0:3]) <= g_epsilon)
            assert(transdist(manipvelocity[3:6],bodyvelocity[3:6]) <= g_epsilon)
            
            # set robot base velocity
            robot.SetVelocity([1,2,3],[4,5,6])
            bodyvelocity = body.GetLinkVelocities()[0]
            manipvelocity = manip.GetVelocity()
            assert(transdist(manipvelocity[0:3] + cross(manipvelocity[3:6],diff),bodyvelocity[0:3]) <= g_epsilon)
            assert(transdist(manipvelocity[3:6],bodyvelocity[3:6]) <= g_epsilon)

#generate_classes(RunRobot, globals(), [('ode','ode'),('bullet','bullet')])

class test_ode(RunRobot):
    def __init__(self):
        RunRobot.__init__(self, 'ode')

# class test_bullet(RunRobot):
#     def __init__(self):
#         RunRobot.__init__(self, 'bullet')
# 
